# -*- coding: utf-8 -*-
"""
Show detailed JSON analysis
"""

import sys
import os
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ml_models.conversation_interest_model import ConversationAnalysisService

# Read the chat file
chat_file = r"c:\Users\avina\Desktop\aura-ai\chat.txt"

messages = []
with open(chat_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Parse format: [TIME] Name: message
        if line.startswith('[') and '] ' in line:
            parts = line.split('] ', 1)
            if len(parts) == 2:
                name_and_msg = parts[1]
                if ':' in name_and_msg:
                    name, message = name_and_msg.split(':', 1)
                    name = name.strip()
                    message = message.strip()
                    
                    # Aarav = You, Maya = Them
                    sender = 'You' if name.lower() == 'aarav' else 'Them'
                    messages.append({'sender': sender, 'message': message})

print("="*80)
print("📊 DETAILED JSON ANALYSIS")
print("="*80)
print()

# Load trained model
model_path = 'ml_models/trained/conversation_interest_model_best.pth'
service = ConversationAnalysisService(model_path if os.path.exists(model_path) else None)
result = service.analyze_conversation(messages)

# Show JSON
print(json.dumps(result, indent=2, ensure_ascii=False))

print("\n" + "="*80)
print("📝 CONVERSATION SAMPLE (First 10 messages)")
print("="*80)
for i, msg in enumerate(messages[:10], 1):
    print(f"{i}. {msg['sender']}: {msg['message']}")
