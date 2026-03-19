"""
Export all stored interview sessions to a CSV file.

Usage:
    # From local files:
    python retrieve.py --data_dir=app/data --output_path=data.csv

    # From remote /retrieve endpoint response:
    python retrieve.py --from_json=remote_data.json --output_path=data.csv
"""

import argparse
import csv
import json
import os


def sessions_from_dir(data_dir: str) -> tuple[list, int]:
    json_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    rows = []
    for filename in sorted(json_files):
        session_id = filename.replace('.json', '')
        with open(os.path.join(data_dir, filename), 'r', encoding='utf-8') as f:
            messages = json.load(f)
        for msg in messages:
            rows.append({'session_id': session_id, **msg})
    return rows, len(json_files)


def sessions_from_json(json_path: str) -> tuple[list, int]:
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # /retrieve returns {session_id: [messages], ...}
    rows = []
    for session_id, messages in data.items():
        for msg in messages:
            rows.append({'session_id': session_id, **msg})
    return rows, len(data)


def write_csv(rows: list, output_path: str, print_chats: bool = False):
    if not rows:
        print("No messages found.")
        return
    if print_chats:
        for row in rows:
            if row.get('type') in ('question', 'answer'):
                role = 'Interviewer' if row['type'] == 'question' else 'Interviewee'
                print(f"[{row.get('session_id')}] {role}: {row.get('content', '')}")
    fieldnames = list(rows[0].keys())
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Export interview sessions to CSV.')
    parser.add_argument('--data_dir', default=None, help='Directory containing session JSON files')
    parser.add_argument('--from_json', default=None, help='JSON file from /retrieve endpoint')
    parser.add_argument('--output_path', required=True, help='Output CSV file path')
    parser.add_argument('--print_chats', action='store_true', help='Print chat messages to stdout')
    args = parser.parse_args()

    if args.from_json:
        rows, n = sessions_from_json(args.from_json)
    else:
        rows, n = sessions_from_dir(args.data_dir or 'app/data')

    write_csv(rows, args.output_path, args.print_chats)
    print(f"Exported {len(rows)} rows from {n} sessions to '{args.output_path}'.")
