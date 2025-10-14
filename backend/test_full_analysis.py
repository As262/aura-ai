# Direct test without API - analyze the decoded conversation

import sys
sys.path.append('.')

from api.conversation_decoder import ConversationDecoder
from ml_models.conversation_interest_model import ConversationAnalysisService
import os

# Decode the chat file
print("🔍 Decoding chat.txt...")
decoder = ConversationDecoder()
decoded = decoder.decode_file(r'c:\Users\avina\Desktop\aura-ai\chat.txt')

print(f"✅ Decoded {decoded['metadata']['total_messages']} messages")
print(f"   Aarav: {sum(1 for m in decoded['messages'] if m['sender'] == 'Aarav')} messages")
print(f"   Maya: {sum(1 for m in decoded['messages'] if m['sender'] == 'Maya')} messages")

# Load model and analyze
print("\n🤖 Loading trained model...")
model_path = 'ml_models/trained/conversation_interest_model_best.pth'
if os.path.exists(model_path):
    print(f"✅ Model found: {model_path}")
else:
    print(f"⚠️  Model not found, using untrained model")
    model_path = None

service = ConversationAnalysisService(model_path)

print("\n🔬 Analyzing conversation...")
result = service.analyze_conversation(decoded['messages'])

# Check for errors
if 'error' in result:
    print(f"\n❌ Error: {result['error']}")
    print(f"   Details: {result}")
else:
    print(f"\n✅ Analysis complete!")
    print(f"\n📊 RESULTS:")
    print(f"   Interest Score: {result['interest_percentage']}%")
    print(f"   Interpretation: {result['interest_interpretation']}")
    print(f"   Confidence: {result['confidence_level']}%")
    print(f"   Total Pairs Analyzed: {result['conversation_pairs_analyzed']}")
    
    # Show formatted text
    print("\n" + "="*80)
    formatted_text = service.format_analysis_as_text(result)
    print(formatted_text)
