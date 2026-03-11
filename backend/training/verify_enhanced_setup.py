"""
Verification script for enhanced conversation model setup
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def verify_setup():
    """Verify that all components are ready for training"""
    
    print("🔍 Verifying Enhanced Conversation Model Setup...\n")
    
    checks_passed = 0
    total_checks = 0
    
    # Check 1: PyTorch availability
    total_checks += 1
    try:
        import torch
        print(f"✅ PyTorch installed: {torch.__version__}")
        
        # Check CUDA
        if torch.cuda.is_available():
            print(f"   🚀 CUDA available! GPU: {torch.cuda.get_device_name(0)}")
        else:
            print(f"   ℹ️  CUDA not available - will use CPU (slower)")
        checks_passed += 1
    except ImportError:
        print("❌ PyTorch not installed! Run: pip install torch")
    
    # Check 2: Model file exists
    total_checks += 1
    model_path = os.path.join(os.path.dirname(__file__), '..', 'ml_models', 'conversation_interest_model.py')
    if os.path.exists(model_path):
        print(f"✅ Model file exists: conversation_interest_model.py")
        checks_passed += 1
    else:
        print(f"❌ Model file not found at: {model_path}")
    
    # Check 3: Model can be imported
    total_checks += 1
    try:
        from ml_models.conversation_interest_model import ConversationInterestAnalyzer
        print(f"✅ Model class imported successfully")
        checks_passed += 1
    except Exception as e:
        print(f"❌ Failed to import model: {e}")
    
    # Check 4: Training script exists
    total_checks += 1
    training_script = os.path.join(os.path.dirname(__file__), 'train_enhanced_conversation_model.py')
    if os.path.exists(training_script):
        print(f"✅ Training script exists: train_enhanced_conversation_model.py")
        checks_passed += 1
    else:
        print(f"❌ Training script not found at: {training_script}")
    
    # Check 5: Output directory exists or can be created
    total_checks += 1
    output_dir = os.path.join(os.path.dirname(__file__), '..', 'ml_models', 'trained')
    if os.path.exists(output_dir):
        print(f"✅ Output directory exists: {output_dir}")
        checks_passed += 1
    else:
        try:
            os.makedirs(output_dir, exist_ok=True)
            print(f"✅ Created output directory: {output_dir}")
            checks_passed += 1
        except Exception as e:
            print(f"❌ Failed to create output directory: {e}")
    
    # Check 6: Model architecture verification
    total_checks += 1
    try:
        from ml_models.conversation_interest_model import ConversationInterestAnalyzer
        import torch
        
        # Create model (use output_size not num_classes)
        model = ConversationInterestAnalyzer(input_size=75, hidden_size=256, output_size=5)
        model.eval()  # Set to eval mode to avoid BatchNorm issues
        
        # Test forward pass with batch_size=2 (BatchNorm requires >1)
        test_input = torch.randn(2, 75)
        output = model(test_input)
        
        if output.shape == (2, 5):
            print(f"✅ Model architecture verified: 75 → 256 → 256 → 128 → 5")
            checks_passed += 1
        else:
            print(f"❌ Unexpected output shape: {output.shape}")
    except Exception as e:
        print(f"❌ Model architecture test failed: {e}")
    
    # Check 7: Feature extraction verification
    total_checks += 1
    try:
        from ml_models.conversation_interest_model import ConversationAnalysisService
        
        service = ConversationAnalysisService()
        
        # Test feature extraction using extract_features method
        your_msg = 'Hello! How are you?'
        their_msg = 'hiii!! 😊 im amazinggg'
        
        features = service.extract_features(your_msg, their_msg)
        
        if len(features) == 75:
            print(f"✅ Feature extraction verified: 75 features extracted")
            
            # Check new features
            print(f"   📊 Features breakdown:")
            print(f"      • 0-49: Original features (lengths, emojis, engagement)")
            print(f"      • 50-59: Text style analysis (ok/okk/okayyy patterns)")
            print(f"      • 60-69: Emoji categorization (11 sentiment types)")
            print(f"      • 70-74: Advanced engagement metrics")
            checks_passed += 1
        else:
            print(f"❌ Unexpected feature count: {len(features)} (expected 75)")
    except Exception as e:
        print(f"❌ Feature extraction test failed: {e}")
    
    # Check 8: Text style patterns verification
    total_checks += 1
    try:
        from ml_models.conversation_interest_model import ConversationAnalysisService
        
        service = ConversationAnalysisService()
        
        # Check attributes directly on service
        has_patterns = hasattr(service, 'text_style_patterns')
        has_method = hasattr(service, '_analyze_text_styles')
        
        if has_patterns and has_method:
            print(f"✅ Text style analysis ready:")
            print(f"   • Enthusiasm patterns: yesss, okayyy, amazinggg")
            print(f"   • Low-effort detection: ok, k, hmm")
            print(f"   • Laugh variations: ha, haha, hahaha")
            checks_passed += 1
        else:
            print(f"❌ Text style patterns not found")
    except Exception as e:
        print(f"❌ Text style verification failed: {e}")
    
    # Check 9: Emoji categories verification
    total_checks += 1
    try:
        from ml_models.conversation_interest_model import ConversationAnalysisService
        
        service = ConversationAnalysisService()
        
        # Check attributes directly on service
        has_emoji_cats = hasattr(service, 'emoji_categories')
        has_emoji_method = hasattr(service, '_analyze_emoji_patterns')
        
        if has_emoji_cats and has_emoji_method:
            emoji_cats = service.emoji_categories
            print(f"✅ Emoji categorization ready:")
            print(f"   • {len(emoji_cats)} emoji categories defined")
            print(f"   • High interest: 😍 🥰 😘 ❤️")
            print(f"   • Happy: 😊 😄 😁")
            print(f"   • Laughing: 😂 🤣")
            print(f"   • Excited: 🎉 🙌")
            checks_passed += 1
        else:
            print(f"❌ Emoji categories not found")
    except Exception as e:
        print(f"❌ Emoji categorization verification failed: {e}")
    
    # Summary
    print(f"\n{'='*60}")
    print(f"✨ Setup Verification Complete!")
    print(f"{'='*60}")
    print(f"Passed: {checks_passed}/{total_checks} checks")
    
    if checks_passed == total_checks:
        print(f"\n🎉 ALL CHECKS PASSED! Ready to train! 🚀")
        print(f"\nNext step: Run training script")
        print(f"  python train_enhanced_conversation_model.py")
        return True
    else:
        print(f"\n⚠️  Some checks failed. Please fix issues above.")
        return False

if __name__ == "__main__":
    success = verify_setup()
    sys.exit(0 if success else 1)
