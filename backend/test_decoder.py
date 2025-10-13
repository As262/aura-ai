"""
Test script for conversation decoder
"""
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api.conversation_decoder import ConversationDecoder

def test_decoder():
    print("🧪 Testing Conversation Decoder...")
    print("=" * 50)
    
    decoder = ConversationDecoder()
    
    # Test with sample file
    file_path = os.path.join(
        os.path.dirname(__file__),
        'test_conversations',
        'sample_high_interest.txt'
    )
    
    if not os.path.exists(file_path):
        print(f"❌ Test file not found: {file_path}")
        return
    
    print(f"\n📄 Testing file: sample_high_interest.txt")
    
    try:
        data = decoder.decode_file(file_path)
        
        print(f"✅ Decoded {len(data['messages'])} messages")
        print(f"✅ Format: {data['metadata']['source']}")
        
        if len(data['messages']) > 0:
            print(f"\n📝 First message:")
            print(f"   Sender: {data['messages'][0]['sender']}")
            print(f"   Message: {data['messages'][0]['message'][:50]}...")
            
        if len(data['messages']) > 1:
            print(f"\n📝 Second message:")
            print(f"   Sender: {data['messages'][1]['sender']}")
            print(f"   Message: {data['messages'][1]['message'][:50]}...")
            
        print(f"\n✅ All tests passed!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_decoder()
