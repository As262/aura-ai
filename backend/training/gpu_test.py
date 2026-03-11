"""
Quick GPU Memory Test
Run this to find optimal batch size for your RTX 3050
"""

import torch
import torchvision.models as models
from torch.cuda.amp import autocast

def test_gpu_memory():
    if not torch.cuda.is_available():
        print("❌ CUDA not available")
        return
    
    device = torch.device('cuda')
    print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
    print(f"💾 Total Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
    
    # Test different batch sizes
    model = models.resnet18(pretrained=True)
    model = model.to(device)
    model.eval()
    
    batch_sizes = [16, 32, 64, 96, 128]
    optimal_batch = 16
    
    for batch_size in batch_sizes:
        try:
            torch.cuda.empty_cache()  # Clear memory
            
            # Create test data
            x = torch.randn(batch_size, 3, 224, 224).to(device)
            
            with autocast():
                output = model(x)
            
            memory_used = torch.cuda.memory_allocated() / 1024**3
            print(f"✅ Batch Size {batch_size:3d}: {memory_used:.1f}GB used")
            optimal_batch = batch_size
            
        except RuntimeError as e:
            if "out of memory" in str(e):
                print(f"❌ Batch Size {batch_size:3d}: Out of memory")
                break
            else:
                raise e
    
    print(f"\n🎯 Recommended batch size for your RTX 3050: {optimal_batch}")
    print(f"💡 Use batch_size={optimal_batch} in your training script")

if __name__ == "__main__":
    test_gpu_memory()