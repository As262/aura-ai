"""Manual API smoke test for a local conversation export.

This file is intentionally safe to import during Django test discovery. Run it
directly and provide an export path when an API server is available.
"""

import argparse
import requests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('conversation_file', help='Path to a conversation export')
    parser.add_argument('--url', default='http://localhost:8000/api/conversation-analysis/')
    args = parser.parse_args()

    with open(args.conversation_file, 'rb') as conversation_file:
        files = {'file': (conversation_file.name, conversation_file, 'text/plain')}
        print("🚀 Sending request to API...")
        response = requests.post(args.url, files=files, timeout=120)

    print(f"\n📊 Status Code: {response.status_code}")
    print("\n📄 Response:")
    print(response.json())


if __name__ == '__main__':
    main()
