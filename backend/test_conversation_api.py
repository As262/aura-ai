"""
Quick test script to verify conversation analysis API is working
"""

import requests
import os

# Test file content
test_conversation = """
[12/01/2024, 10:30:45] John: Hey! How are you doing?
[12/01/2024, 10:31:12] Sarah: I'm doing great! Just finished a project. How about you?
[12/01/2024, 10:31:45] John: Nice! What was the project about?
[12/01/2024, 10:32:30] Sarah: It was a web app for tracking fitness goals. Really proud of how it turned out! 🎉
[12/01/2024, 10:33:00] John: That sounds amazing! Can I see it?
[12/01/2024, 10:33:45] Sarah: Sure! I'll send you the link. What have you been up to?
[12/01/2024, 10:34:20] John: Working on some AI stuff. Pretty interesting!
[12/01/2024, 10:35:00] Sarah: Oh wow! AI is so cool! What kind of AI? Tell me more! 😊
[12/01/2024, 10:35:45] John: Machine learning models for image analysis
[12/01/2024, 10:36:30] Sarah: That's really impressive! Are you using TensorFlow or PyTorch?
"""

def test_conversation_analysis():
    """Test the conversation analysis endpoint"""
    
    # Create temporary test file
    test_file_path = 'test_convo.txt'
    with open(test_file_path, 'w', encoding='utf-8') as f:
        f.write(test_conversation)
    
    try:
        print("🧪 Testing Conversation Analysis API...")
        print("=" * 50)
        
        # Test endpoint
        url = 'http://localhost:8000/api/conversation-analysis/'
        
        with open(test_file_path, 'rb') as f:
            files = {'file': ('test_convo.txt', f, 'text/plain')}
            data = {'platform': 'instagram'}
            
            print(f"📤 Sending request to {url}")
            response = requests.post(url, files=files, data=data)
            
            print(f"📥 Response status: {response.status_code}")
            print(f"📥 Response headers: {dict(response.headers)}")
            
            if response.status_code == 201:
                result = response.json()
                print("\n✅ SUCCESS! Analysis completed:")
                print("=" * 50)
                
                if 'analysis' in result:
                    analysis = result['analysis']
                    print(f"\n📊 Interest Level: {analysis.get('overall_interest_level', 'N/A')}")
                    print(f"📊 Interest Percentage: {analysis.get('interest_percentage', 'N/A')}%")
                    print(f"📊 Total Messages: {analysis.get('total_messages', 'N/A')}")
                    print(f"📊 Your Messages: {analysis.get('your_messages', 'N/A')}")
                    print(f"📊 Their Messages: {analysis.get('their_messages', 'N/A')}")
                    
                    if 'engagement_metrics' in analysis:
                        print("\n💬 Engagement Metrics:")
                        metrics = analysis['engagement_metrics']
                        for key, value in metrics.items():
                            print(f"   {key}: {value}")
                    
                    if 'improvement_suggestions' in analysis:
                        print("\n💡 Suggestions:")
                        for i, suggestion in enumerate(analysis['improvement_suggestions'][:3], 1):
                            print(f"\n   {i}. [{suggestion.get('priority', 'N/A')}] {suggestion.get('category', 'N/A')}")
                            print(f"      {suggestion.get('suggestion', 'N/A')}")
                
                print("\n" + "=" * 50)
                print("✅ Test PASSED!")
                
            else:
                print(f"\n❌ Test FAILED!")
                print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"\n❌ Error during test: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up test file
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"\n🧹 Cleaned up test file")


def test_health_check():
    """Test if backend is running"""
    try:
        print("\n🏥 Testing Backend Health...")
        response = requests.get('http://localhost:8000/api/health/', timeout=5)
        
        if response.status_code == 200:
            print("✅ Backend is running!")
            data = response.json()
            print(f"   Status: {data.get('status', 'N/A')}")
            print(f"   GPU Available: {data.get('gpu_status', {}).get('available', False)}")
            return True
        else:
            print(f"⚠️ Backend returned status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to backend!")
        print("   Make sure the Django server is running:")
        print("   cd backend && python manage.py runserver")
        return False
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "🚀 Aura AI - Conversation Analysis Test" + "\n")
    
    # First check if backend is running
    if test_health_check():
        print()
        # Then run the actual test
        test_conversation_analysis()
    else:
        print("\n⚠️ Please start the backend server first:")
        print("   cd backend")
        print("   python manage.py runserver")
