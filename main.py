import requests
import json
from urllib.parse import urlparse, parse_qs
import re
import pandas as pd
from datetime import datetime

def send_request(url, params=None, data=None, headers=None):
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error making request: {e}")
        return None

def main():
    # Your target URL
    url = "http://192.168.3.205/web_routine/index.php"
    
  
    schedule = {}
    file_path = 'students.txt'

    with open(file_path, 'r') as file:
        for line in file:
            # Use .strip() to remove leading/trailing whitespace, including the newline character
            id = line.strip()
            params = {
                'idno': id
            }


            # Send the request
            response = send_request(url, params=params)
            
            if response:
                last_table = response.text[response.text.rfind("<table"):response.text.rfind("<tr>")]
                matches = list(re.finditer(r"<tr", last_table))
                last_table = last_table[matches[1].start():]
                matches = re.findall(r'<td>([A-Z][a-z]+day)</td>\s*<td>([0-9]{2}:[0-9]{2}[ap]m [0-9]{2}:[0-9]{2}[ap]m)</td>', last_table)

                for day, time in matches:
                    key = f"{day}: {time}"
                    schedule[key] = schedule.get(key, 0) + 1
            else:
                print("Failed")
    
    # Parse into DataFrame
    records = []
    for key, count in schedule.items():
        day, time_slot = key.split(': ', 1)
        records.append({'day': day.strip(), 'time_slot': time_slot.strip(), 'count': count})

    df = pd.DataFrame(records)

    # Order days
    day_order = ['Friday', 'Saturday', 'Sunday', 'Monday', 'Tuesday', 'Wednesday']
    df['day'] = pd.Categorical(df['day'], categories=day_order, ordered=True)
    df = df.sort_values('day')

    # Sort time slots chronologically
    def parse_start_time(slot):
        start = slot.split(' ')[0]
        return datetime.strptime(start, '%I:%M%p')

    df['start_time'] = df['time_slot'].apply(parse_start_time)
    df = df.sort_values(['day', 'start_time']).drop('start_time', axis=1)

    # Pivot table
    pivot = df.pivot(index='day', columns='time_slot', values='count').fillna(0).astype(int)

    # Reorder columns by chronological order
    unique_slots = sorted(df['time_slot'].unique(), key=parse_start_time)
    pivot = pivot[unique_slots]

    # Save to CSV
    pivot.to_csv('schedule_pivot.csv')





if __name__ == "__main__":
    main()