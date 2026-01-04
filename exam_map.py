import requests
import json
from urllib.parse import urlparse, parse_qs
import re
import pandas as pd
from datetime import datetime

def send_post_request(url, params=None, data=None, headers=None):
    try:
        response = requests.post(url, data=data, params=params, headers=headers, timeout=30)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def main():
    # Your target URL
    url = "http://192.168.3.205/final_exam_schedule/student_exam_routine.php"

    schedule = {}
    file_path = 'students.txt'
    with open(file_path, 'r') as file:
        for line in file:
            id = line.strip()
            data = {
                "id": id,
                "submit": "Submit"
            }
            
            response = send_post_request(url, data=data)
            if response:
                last_table = response.text[response.text.rfind("<table"):response.text.rfind("</table>")]
                last_table = response.text[response.text.rfind("</thead>"):response.text.rfind("<tr>")]

                pattern = re.compile(
                    r"<td[^>]*>\s*<center>\s*"
                    r"(\d{4}-\d{2}-\d{2})\s*\(\w+\)\s*"
                    r"</center>\s*</td>\s*"
                    r"<td[^>]*>\s*<center>\s*"
                    r"([0-9]{2}:[0-9]{2}[ap]m-[0-9]{2}:[0-9]{2}[ap]m)"
                    r"\s*</center>\s*</td>",
                    re.IGNORECASE
                )

                matches = pattern.findall(last_table)
                for date_str, time_slot in matches:
                    key = (date_str, time_slot)   # tuple
                    schedule[key] = schedule.get(key, 0) + 1
            else:
                print("Failed")
    
    records = []
    for key, count in schedule.items():
        date_str, time_slot = key
        records.append({'date': date_str.strip(), 'time_slot': time_slot.strip(), 'count': count})

    df = pd.DataFrame(records)

    from datetime import datetime

    # Convert date column to datetime
    df['date'] = pd.to_datetime(df['date'])

    pivot_df = (
        df.pivot_table(
            index='date',
            columns='time_slot',
            values='count',
            aggfunc='sum',
            fill_value=0
        )
    )

    # Order time columns chronologically
    def parse_start_time(slot):
        return datetime.strptime(slot.split('-', 1)[0].strip(), "%I:%M%p")

    ordered_slots = sorted(pivot_df.columns, key=parse_start_time)
    pivot_df = pivot_df[ordered_slots]

    # Save pivoted CSV
    pivot_df.to_csv("schedule_pivot.csv", date_format="%Y-%m-%d")




if __name__ == "__main__":
    main()