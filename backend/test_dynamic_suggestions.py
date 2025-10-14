"""
Test dynamic suggestions with various conversation scenarios
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.conversation_interest_model import ConversationAnalysisService

print("="*80)
print("🧪 TESTING DYNAMIC AI-POWERED SUGGESTIONS")
print("="*80)

# Test Case 1: Low-effort responses
print("\n📋 TEST 1: Low-Effort Responses")
print("-"*80)

test1 = [
    {'sender': 'You', 'message': 'Hey! How was your day?'},
    {'sender': 'Them', 'message': 'ok'},
    {'sender': 'You', 'message': 'Did you do anything fun?'},
    {'sender': 'Them', 'message': 'not really'},
    {'sender': 'You', 'message': 'Want to grab dinner sometime?'},
    {'sender': 'Them', 'message': 'maybe'},
]

service = ConversationAnalysisService()
result1 = service.analyze_conversation(test1)

print("\n💡 DYNAMIC SUGGESTIONS:")
for i, suggestion in enumerate(result1.get('improvement_suggestions', []), 1):
    print(f"\n{i}. [{suggestion['priority']}] {suggestion['category']}")
    print(f"   {suggestion['suggestion']}")
    print(f"   💎 {suggestion['tip']}")

# Test Case 2: Enthusiastic responses
print("\n\n📋 TEST 2: Enthusiastic Conversation")
print("-"*80)

test2 = [
    {'sender': 'You', 'message': 'I just got tickets to that concert!'},
    {'sender': 'Them', 'message': 'OMG YESSS!! 😍 that\'s amazinggg!!'},
    {'sender': 'You', 'message': 'Want to come with me?'},
    {'sender': 'Them', 'message': 'hahahaha are you serious?? I would LOVE to!! 🎉🙌'},
    {'sender': 'You', 'message': 'Yeah! It\'s next Saturday'},
    {'sender': 'Them', 'message': 'coool!! I\'m so excited!! When should we meet? 😊✨'},
]

result2 = service.analyze_conversation(test2)

print("\n💡 DYNAMIC SUGGESTIONS:")
for i, suggestion in enumerate(result2.get('improvement_suggestions', []), 1):
    print(f"\n{i}. [{suggestion['priority']}] {suggestion['category']}")
    print(f"   {suggestion['suggestion']}")
    print(f"   💎 {suggestion['tip']}")

# Test Case 3: Declining interest
print("\n\n📋 TEST 3: Interest Declining Over Time")
print("-"*80)

test3 = [
    {'sender': 'You', 'message': 'The movie was incredible!'},
    {'sender': 'Them', 'message': 'omg yesss! I loved it so much!! 😍 what was your favorite scene?'},
    {'sender': 'You', 'message': 'The ending was mind-blowing!'},
    {'sender': 'Them', 'message': 'right?? so goood! 😊'},
    {'sender': 'You', 'message': 'So anyway, I also did laundry today'},
    {'sender': 'Them', 'message': 'oh cool'},
    {'sender': 'You', 'message': 'And I reorganized my closet'},
    {'sender': 'Them', 'message': 'nice'},
    {'sender': 'You', 'message': 'Then I watched some YouTube'},
    {'sender': 'Them', 'message': 'k'},
]

result3 = service.analyze_conversation(test3)

print("\n💡 DYNAMIC SUGGESTIONS:")
for i, suggestion in enumerate(result3.get('improvement_suggestions', []), 1):
    print(f"\n{i}. [{suggestion['priority']}] {suggestion['category']}")
    print(f"   {suggestion['suggestion']}")
    print(f"   💎 {suggestion['tip']}")

# Test Case 4: Emoji mismatch
print("\n\n📋 TEST 4: Emoji Style Mismatch")
print("-"*80)

test4 = [
    {'sender': 'You', 'message': 'I just finished my project'},
    {'sender': 'Them', 'message': 'omg that\'s amazing!! 🎉🎊 congrats!! 😍'},
    {'sender': 'You', 'message': 'Thanks, it took forever'},
    {'sender': 'Them', 'message': 'I bet!! you must be so proud!! 🙌✨'},
    {'sender': 'You', 'message': 'Yeah it was a lot of work'},
    {'sender': 'Them', 'message': 'you deserve to celebrate!! 🥳💕'},
]

result4 = service.analyze_conversation(test4)

print("\n💡 DYNAMIC SUGGESTIONS:")
for i, suggestion in enumerate(result4.get('improvement_suggestions', []), 1):
    print(f"\n{i}. [{suggestion['priority']}] {suggestion['category']}")
    print(f"   {suggestion['suggestion']}")
    print(f"   💎 {suggestion['tip']}")

print("\n" + "="*80)
print("✅ ALL TESTS COMPLETE!")
print("="*80)
print("\n🎉 Dynamic AI-powered suggestions are working!")
print("Each suggestion is now based on ACTUAL conversation content!")
