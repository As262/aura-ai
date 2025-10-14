# Test the conversation decoder directly

import sys
sys.path.append('.')

from api.conversation_decoder import ConversationDecoder

decoder = ConversationDecoder()
decoded = decoder.decode_file(r'c:\Users\avina\Desktop\aura-ai\chat.txt')

print(f"📊 Total messages: {decoded['metadata']['total_messages']}")
print(f"\n📝 First 5 messages:")
for i, msg in enumerate(decoded['messages'][:5], 1):
    print(f"{i}. Sender: '{msg['sender']}' | Message: '{msg['message'][:50]}...'")

print(f"\n📊 Message count by sender:")
senders = {}
for msg in decoded['messages']:
    sender = msg['sender']
    senders[sender] = senders.get(sender, 0) + 1

for sender, count in senders.items():
    print(f"  {sender}: {count} messages")

print(f"\n🔍 Checking for conversation pairs...")
pairs = 0
for i in range(len(decoded['messages']) - 1):
    curr = decoded['messages'][i]
    next_msg = decoded['messages'][i + 1]
    if curr['sender'] != next_msg['sender']:
        pairs += 1
        if pairs <= 3:
            print(f"  Pair {pairs}: {curr['sender']} -> {next_msg['sender']}")

print(f"\n✅ Total pairs where sender changes: {pairs}")
