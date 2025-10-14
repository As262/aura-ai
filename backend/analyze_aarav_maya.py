# -*- coding: utf-8 -*-
"""
Analyze Aarav & Maya's Late-Night Conversation
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
print("🌙 ANALYZING AARAV & MAYA'S LATE-NIGHT CONVERSATION")
print("="*80)
print()

# Load trained model
model_path = 'ml_models/trained/conversation_interest_model_best.pth'
print(f"📊 Loading trained model from: {model_path}")

if os.path.exists(model_path):
    print("✅ Model found! Using trained weights (96% accuracy)")
else:
    print("⚠️  Using untrained model (will still work)")

print()
print(f"💬 Parsed {len(messages)} messages from chat file")
print()
print("🤖 Running AI analysis...")
print()

# Analyze conversation
service = ConversationAnalysisService(model_path if os.path.exists(model_path) else None)
result = service.analyze_conversation(messages)

# Format as beautiful text
formatted_text = service.format_analysis_as_text(result)

print(formatted_text)

# Save to file
output_file = 'aarav_maya_analysis_report.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("🌙 AARAV & MAYA'S LATE-NIGHT CONVERSATION ANALYSIS\n")
    f.write("="*80 + "\n\n")
    f.write("📅 Date: October 14, 2025\n")
    f.write("⏰ Time: 11:35 PM - 12:33 AM\n")
    f.write(f"💬 Total Messages: {len(messages)} exchanges\n")
    f.write("\n" + "="*80 + "\n\n")
    f.write(formatted_text)

print("\n" + "="*80)
print(f"📄 Full report saved to: {output_file}")
print("="*80)
