"""
Training Pipeline for Composition Detection Model
"""

import os
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import json
from pathlib import Path
import sys
from torch.cuda.amp import GradScaler, autocast

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from ml_models.composition_model import CompositionCNN


class CompositionDataset(Dataset):
    """
    Custom dataset for composition images
    
    Expected folder structure:
    training_data/
        rule_of_thirds/
            img1.jpg
            img2.jpg
        centered/
            img1.jpg
        leading_lines/
            img1.jpg
        ...
    """
    
    def __init__(self, root_dir, transform=None):
        self.root_dir = Path(root_dir)
        self.transform = transform
        
        self.composition_types = [
            'rule_of_thirds',
            'centered',
            'leading_lines',
            'diagonal',
            'symmetrical',
            'golden_ratio',
            'fill_the_frame',
            'frame_within_frame'
        ]
        
        # Collect all images
        self.images = []
        self.labels = []
        
        for idx, comp_type in enumerate(self.composition_types):
            comp_dir = self.root_dir / comp_type
            if comp_dir.exists():
                for ext in ['*.jpg', '*.jpeg', '*.png', '*.JPG', '*.JPEG', '*.PNG']:
                    for img_path in comp_dir.glob(ext):
                        self.images.append(str(img_path))
                        self.labels.append(idx)
        
        print(f"📊 Loaded {len(self.images)} images across {len(self.composition_types)} classes")
        for idx, comp_type in enumerate(self.composition_types):
            count = self.labels.count(idx)
            print(f"  - {comp_type}: {count} images")
    
    def __len__(self):
        return len(self.images)
    
    def __getitem__(self, idx):
        image_path = self.images[idx]
        label = self.labels[idx]
        
        try:
            image = Image.open(image_path).convert('RGB')
        except Exception as e:
            print(f"⚠️ Failed to load {image_path}: {e}")
            # Return a blank image as fallback
            image = Image.new('RGB', (224, 224), color='black')
        
        if self.transform:
            image = self.transform(image)
        
        return image, label


def train_composition_model(
    data_dir='training_data',
    epochs=200,
    batch_size=128,  # Optimal balance for RTX 3050 6GB + i5-13450HX
    learning_rate=0.001,
    save_dir='ml_models/trained',
    device=None,
    resume_from_checkpoint=None,
    save_checkpoint_every=10
):
    """
    Train the composition detection model
    
    Args:
        data_dir: Directory containing training images
        epochs: Number of training epochs
        batch_size: Batch size
        learning_rate: Learning rate
        save_dir: Where to save trained model
        device: cuda or cpu
    """
    
    if device is None:
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    print(f"🚀 Training on device: {device}")
    
    # Optimize GPU performance
    if device.type == 'cuda':
        torch.backends.cudnn.benchmark = True  # Optimize for consistent input sizes
        torch.backends.cuda.matmul.allow_tf32 = True  # Use TensorFloat-32 for faster training
        print(f"🎮 GPU: {torch.cuda.get_device_name(0)}")
        print(f"💾 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f}GB")
    
    # Data augmentation for training
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop((224, 224)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], 
                           std=[0.229, 0.224, 0.225])
    ])
    
    # Load dataset
    dataset = CompositionDataset(data_dir, transform=train_transform)
    
    if len(dataset) == 0:
        print("❌ No training data found!")
        print(f"📁 Please add images to: {Path(data_dir).absolute()}")
        return None, None
    
    # Split train/val (80/20) with fixed seed for reproducibility
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    
    # Use fixed seed to ensure consistent splits across resume sessions
    generator = torch.Generator()
    generator.manual_seed(42)  # Fixed seed for reproducible splits
    
    train_dataset, val_dataset = torch.utils.data.random_split(
        dataset, [train_size, val_size], generator=generator
    )
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, 
                              num_workers=8, pin_memory=True, persistent_workers=True,
                              prefetch_factor=2)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, 
                           num_workers=8, pin_memory=True, persistent_workers=True,
                           prefetch_factor=2)
    
    print(f"📦 Train: {train_size} images, Val: {val_size} images")
    
    # Initialize model
    model = CompositionCNN(num_classes=10, pretrained=True)
    model = model.to(device)
    
    # Loss and optimizer
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-4)
    scheduler = optim.lr_scheduler.StepLR(optimizer, step_size=15, gamma=0.1)
    
    # Mixed precision training for better GPU utilization
    scaler = GradScaler() if device.type == 'cuda' else None
    if scaler:
        print("⚡ Using mixed precision training for better GPU performance")
    
    # Initialize training variables
    best_val_acc = 0.0
    start_epoch = 0
    history = {'train_loss': [], 'train_acc': [], 'val_loss': [], 'val_acc': []}
    
    # Resume from checkpoint if provided
    if resume_from_checkpoint and os.path.exists(resume_from_checkpoint):
        print(f"📂 Loading checkpoint from {resume_from_checkpoint}")
        checkpoint = torch.load(resume_from_checkpoint, map_location=device)
        model.load_state_dict(checkpoint['model_state_dict'])
        optimizer.load_state_dict(checkpoint['optimizer_state_dict'])
        scheduler.load_state_dict(checkpoint['scheduler_state_dict'])
        start_epoch = checkpoint['epoch'] + 1
        best_val_acc = checkpoint['best_val_acc']
        history = checkpoint['history']
        print(f"✅ Resumed from epoch {start_epoch}, best val acc: {best_val_acc:.2f}%")
    
    # Training loop
    for epoch in range(start_epoch, epochs):
        # Training phase
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0
        
        for images, labels in train_loader:
            images, labels = images.to(device, non_blocking=True), labels.to(device, non_blocking=True)
            
            optimizer.zero_grad(set_to_none=True)  # More efficient than zero_grad()
            
            if scaler:  # Mixed precision training
                with autocast():
                    outputs = model(images)
                    loss = criterion(outputs, labels)
                
                scaler.scale(loss).backward()
                scaler.step(optimizer)
                scaler.update()
            else:  # Regular training
                outputs = model(images)
                loss = criterion(outputs, labels)
                loss.backward()
                optimizer.step()
            
            running_loss += loss.item()
            _, predicted = outputs.max(1)
            total += labels.size(0)
            correct += predicted.eq(labels).sum().item()
        
        train_loss = running_loss / len(train_loader)
        train_acc = 100.0 * correct / total
        
        # Validation phase
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        
        with torch.no_grad():
            for images, labels in val_loader:
                images, labels = images.to(device, non_blocking=True), labels.to(device, non_blocking=True)
                
                if scaler:  # Use autocast for validation too
                    with autocast():
                        outputs = model(images)
                        loss = criterion(outputs, labels)
                else:
                    outputs = model(images)
                    loss = criterion(outputs, labels)
                
                val_loss += loss.item()
                _, predicted = outputs.max(1)
                total += labels.size(0)
                correct += predicted.eq(labels).sum().item()
        
        val_loss = val_loss / len(val_loader)
        val_acc = 100.0 * correct / total
        
        # Update learning rate
        scheduler.step()
        
        # Save history
        history['train_loss'].append(train_loss)
        history['train_acc'].append(train_acc)
        history['val_loss'].append(val_loss)
        history['val_acc'].append(val_acc)
        
        print(f"Epoch [{epoch+1}/{epochs}] "
              f"Train Loss: {train_loss:.4f}, Train Acc: {train_acc:.2f}% | "
              f"Val Loss: {val_loss:.4f}, Val Acc: {val_acc:.2f}%")
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            os.makedirs(save_dir, exist_ok=True)
            model_path = os.path.join(save_dir, 'composition_model_best.pth')
            torch.save(model.state_dict(), model_path)
            print(f"✅ Saved best model (Val Acc: {val_acc:.2f}%)")
        
        # Save checkpoint every N epochs
        if (epoch + 1) % save_checkpoint_every == 0:
            os.makedirs(save_dir, exist_ok=True)
            checkpoint_path = os.path.join(save_dir, f'checkpoint_epoch_{epoch+1}.pth')
            torch.save({
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'scheduler_state_dict': scheduler.state_dict(),
                'best_val_acc': best_val_acc,
                'history': history,
                'train_loss': train_loss,
                'val_loss': val_loss,
                'train_acc': train_acc,
                'val_acc': val_acc
            }, checkpoint_path)
            print(f"💾 Saved checkpoint at epoch {epoch+1}")
            
            # Keep only last 3 checkpoints to save disk space
            checkpoint_files = sorted([f for f in os.listdir(save_dir) if f.startswith('checkpoint_epoch_')])
            if len(checkpoint_files) > 3:
                old_checkpoint = os.path.join(save_dir, checkpoint_files[0])
                os.remove(old_checkpoint)
                print(f"🗑️ Removed old checkpoint: {checkpoint_files[0]}")
    
    # Save final model
    final_model_path = os.path.join(save_dir, 'composition_model_final.pth')
    torch.save(model.state_dict(), final_model_path)
    
    # Save training history
    history_path = os.path.join(save_dir, 'training_history.json')
    with open(history_path, 'w') as f:
        json.dump(history, f, indent=2)
    
    print(f"\n🎉 Training complete!")
    print(f"Best validation accuracy: {best_val_acc:.2f}%")
    print(f"Model saved to: {save_dir}")
    
    return model, history


if __name__ == "__main__":
    print("🎨 Aura AI - Composition Model Training")
    print("="*70)
    
    # Check if user wants to resume from checkpoint
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--resume":
        # Find latest checkpoint
        save_dir = 'ml_models/trained'
        if os.path.exists(save_dir):
            checkpoint_files = sorted([f for f in os.listdir(save_dir) if f.startswith('checkpoint_epoch_')])
            if checkpoint_files:
                latest_checkpoint = os.path.join(save_dir, checkpoint_files[-1])
                print(f"🔄 Found checkpoint: {checkpoint_files[-1]}")
                
                # Resume training
                train_composition_model(
                    data_dir='training_data',
                    epochs=200,
                    batch_size=128,
                    learning_rate=0.001,
                    resume_from_checkpoint=latest_checkpoint,
                    save_checkpoint_every=10
                )
            else:
                print("❌ No checkpoints found. Starting from scratch.")
                train_composition_model(
                    data_dir='training_data',
                    epochs=200,
                    batch_size=128,
                    learning_rate=0.001,
                    save_checkpoint_every=10
                )
        else:
            print("❌ No trained models directory found. Starting from scratch.")
            train_composition_model(
                data_dir='training_data',
                epochs=200,
                batch_size=32,
                learning_rate=0.001,
                save_checkpoint_every=10
            )
    else:
        # Normal training from scratch
        print("🚀 Starting training from scratch...")
        print("💡 Use 'python train_model.py --resume' to resume from checkpoint")
        print()
        
        train_composition_model(
            data_dir='training_data',
            epochs=200,
            batch_size=128,
            learning_rate=0.001,
            save_checkpoint_every=10
        )
 