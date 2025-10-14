# Test the conversation analysis API with chat.txt

import requests

# Read the chat file
with open(r'c:\Users\avina\Desktop\aura-ai\chat.txt', 'rb') as f:
    files = {'file': ('chat.txt', f, 'text/plain')}
    
    print("🚀 Sending request to API...")
    response = requests.post(
        'http://localhost:8000/api/conversation-analysis/',
        files=files
    )
    
print(f"\n📊 Status Code: {response.status_code}")
print(f"\n📄 Response:")
print(response.json())
