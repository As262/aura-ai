"""
Test script to see the formatted text output
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.conversation_interest_model import ConversationAnalysisService

# Sample conversation
test_messages = [
    {'sender': 'You', 'message': 'Hey! How was your day?'},
    {'sender': 'Them', 'message': 'omg it was amazinggg!! 😍'},
    {'sender': 'You', 'message': 'Really? Tell me about it!'},
    {'sender': 'Them', 'message': 'yessss so i went to this new place and it was so coool 😊✨'},
    {'sender': 'You', 'message': 'That sounds awesome! What did you like most about it?'},
    {'sender': 'Them', 'message': 'hahahaha everything!! the vibes were 🔥🔥'},
    {'sender': 'You', 'message': 'Nice! We should go together sometime'},
    {'sender': 'Them', 'message': 'OMG YESSS!! 🥰 that would be amazing!!'},
]

print("🧪 Testing Formatted Text Output\n")

# Create service
service = ConversationAnalysisService()

# Analyze conversation
print("📊 Analyzing conversation...")
result = service.analyze_conversation(test_messages)

# Format as text
print("\n" + "="*80)
print("FORMATTED TEXT OUTPUT:")
print("="*80 + "\n")

formatted_text = service.format_analysis_as_text(result)
print(formatted_text)

print("\n\n" + "="*80)
print("✅ TEST COMPLETE!")
print("="*80)
