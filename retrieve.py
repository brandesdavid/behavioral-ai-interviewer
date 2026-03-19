"""
Export all stored interview sessions to a CSV file.

Usage:
    python retrieve.py --data_dir=app/data --output_path=data.csv
"""

import argparse
import csv
import json
import os


def retrieve_all_sessions(data_dir: str, output_path: str, print_chats: bool = False):
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    if not json_files:
        print(f"No sessions found in '{data_dir}'.")
        return

    rows = []
    for filename in sorted(json_files):
        session_id = filename.replace('.json', '')
        with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
            messages = json.load(f)
        for msg in messages:
            row = {'session_id': session_id, **msg}
            rows.append(row)
            if print_chats and msg.get('type') in ('question', 'answer'):
                role = 'Interviewer' if msg['type'] == 'question' else 'Interviewee'
                print(f"[{session_id}] {role}: {msg.get('content', '')}")

    if not rows:
        print("No messages found.")
        return

    fieldnames = list(rows[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)

    print(f"Exported {len(rows)} rows from {len(json_files)} sessions to '{output_path}'.")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export interview sessions to CSV.')
    parser.add_argument('--data_dir', default='app/data', help='Directory containing session JSON files')
    parser.add_argument('--output_path', required=True, help='Output CSV file path')
    parser.add_argument('--print_chats', action='store_true', help='Print chat messages to stdout')
    args = parser.parse_args()
    retrieve_all_sessions(args.data_dir, args.output_path, args.print_chats)
