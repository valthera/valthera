# custom_behavior_trainer.py
import os
import json
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import Dataset, DataLoader
import numpy as np
from decord import VideoReader
import pandas as pd

# Import V-JEPA 2 modules
from src.models.attentive_pooler import AttentiveClassifier
from src.models.vision_transformer import vit_giant_xformers_rope

# Your custom behavior classes
BEHAVIOR_CLASSES = {
    0: "about_to_move_hat",
    1: "about_to_move_knife"
}

IMAGENET_DEFAULT_MEAN = (0.485, 0.456, 0.406)
IMAGENET_DEFAULT_STD = (0.229, 0.224, 0.225)

class CustomBehaviorDataset(Dataset):
    def __init__(self, data_dir, transform=None):
        self.data_dir = data_dir
        self.transform = transform
        self.samples = []
        self.labels = []
        
        # Load samples from directories
        for class_id, class_name in BEHAVIOR_CLASSES.items():
            class_dir = os.path.join(data_dir, class_name)
            if os.path.exists(class_dir):
                for video_file in os.listdir(class_dir):
                    if video_file.endswith('.mp4'):
                        video_path = os.path.join(class_dir, video_file)
                        self.samples.append(video_path)
                        self.labels.append(class_id)
        
        print(f"Loaded {len(self.samples)} videos:")
        for class_id, class_name in BEHAVIOR_CLASSES.items():
            count = sum(1 for label in self.labels if label == class_id)
            print(f"  {class_name}: {count} videos")
    
    def __len__(self):
        return len(self.samples)
    
    def __getitem__(self, idx):
        video_path = self.samples[idx]
        label = self.labels[idx]
        
        # Load video
        vr = VideoReader(video_path)
        frame_idx = np.arange(0, min(len(vr), 128), 2)  # Sample up to 64 frames
        video = vr.get_batch(frame_idx).asnumpy()  # T x H x W x C
        
        # Apply transform if provided
        if self.transform:
            video = self.transform(video)
        else:
            # Apply default transform
            video = simple_video_transform(video)
        
        return video, label

def simple_video_transform(video, img_size=384):
    """
    Transform video to tensor format expected by V-JEPA 2
    """
    # video is T x H x W x C (numpy array)
    video = torch.from_numpy(video).float() / 255.0  # Normalize to [0, 1]
    video = video.permute(0, 3, 1, 2)  # T x C x H x W
    
    # Resize if needed
    T, C, H, W = video.shape
    if H != img_size or W != img_size:
        video = F.interpolate(video, size=(img_size, img_size), mode='bilinear', align_corners=False)
    
    # Normalize with ImageNet stats
    mean = torch.tensor(IMAGENET_DEFAULT_MEAN, dtype=torch.float32).view(1, 3, 1, 1)
    std = torch.tensor(IMAGENET_DEFAULT_STD, dtype=torch.float32).view(1, 3, 1, 1)
    video = (video - mean) / std
    
    # Reshape to match expected input format: [C, T, H, W] (no batch dimension)
    video = video.permute(1, 0, 2, 3)  # C x T x H x W
    
    return video

def load_pretrained_vjepa_encoder():
    """Load and freeze the V-JEPA 2 encoder"""
    print("Loading V-JEPA 2 encoder...")
    
    # Initialize model
    encoder = vit_giant_xformers_rope(img_size=(384, 384), num_frames=64)
    
    # Load pre-trained weights
    pretrained_dict = torch.load("./vitg-384.pt", weights_only=True, map_location="cpu")["encoder"]
    pretrained_dict = {k.replace("module.", ""): v for k, v in pretrained_dict.items()}
    pretrained_dict = {k.replace("backbone.", ""): v for k, v in pretrained_dict.items()}
    encoder.load_state_dict(pretrained_dict, strict=False)
    
    # Freeze the encoder
    for param in encoder.parameters():
        param.requires_grad = False
    
    encoder.eval()
    print("V-JEPA 2 encoder loaded and frozen")
    return encoder

def create_custom_classifier(embed_dim=1408):
    """Create custom classifier head"""
    classifier = AttentiveClassifier(
        embed_dim=embed_dim,
        num_heads=16,
        depth=4,
        num_classes=len(BEHAVIOR_CLASSES),  # 2 classes
        use_activation_checkpointing=True,
    )
    return classifier

def train_custom_classifier():
    """Main training function"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")
    
    # Create dataset
    print("Creating dataset...")
    dataset = CustomBehaviorDataset("/workspace/vjepa2/data")
    
    # Split into train/val (80/20)
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = torch.utils.data.random_split(dataset, [train_size, val_size])
    
    # Create data loaders
    train_loader = DataLoader(train_dataset, batch_size=2, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_dataset, batch_size=2, shuffle=False, num_workers=0)
    
    print(f"Train samples: {len(train_dataset)}, Val samples: {len(val_dataset)}")
    
    # Load models
    encoder = load_pretrained_vjepa_encoder().to(device)
    classifier = create_custom_classifier().to(device)
    
    # Training setup
    optimizer = torch.optim.AdamW(classifier.parameters(), lr=1e-4, weight_decay=0.01)
    criterion = nn.CrossEntropyLoss()
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=50)
    
    # Training loop
    best_val_acc = 0.0
    print("\nStarting training...")
    
    for epoch in range(10):  # Adjust epochs as needed
        # Training phase
        classifier.train()
        train_loss = 0.0
        train_correct = 0
        train_total = 0
        
        for batch_idx, (videos, labels) in enumerate(train_loader):
            videos = videos.to(device)
            labels = labels.to(device)
            
            optimizer.zero_grad()
            
            # Forward pass through frozen encoder
            with torch.no_grad():
                features = encoder(videos)  # Extract features
            
            # Forward pass through classifier
            logits = classifier(features)
            loss = criterion(logits, labels)
            
            # Backward pass
            loss.backward()
            optimizer.step()
            
            # Statistics
            train_loss += loss.item()
            _, predicted = torch.max(logits.data, 1)
            train_total += labels.size(0)
            train_correct += (predicted == labels).sum().item()
            
            if batch_idx % 5 == 0:
                print(f'Epoch {epoch+1}, Batch {batch_idx}, Loss: {loss.item():.4f}')
        
        # Validation phase
        classifier.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0
        
        with torch.no_grad():
            for videos, labels in val_loader:
                videos = videos.to(device)
                labels = labels.to(device)
                
                features = encoder(videos)
                logits = classifier(features)
                loss = criterion(logits, labels)
                
                val_loss += loss.item()
                _, predicted = torch.max(logits.data, 1)
                val_total += labels.size(0)
                val_correct += (predicted == labels).sum().item()
        
        # Calculate accuracies
        train_acc = 100.0 * train_correct / train_total
        val_acc = 100.0 * val_correct / val_total
        
        print(f'Epoch {epoch+1}: Train Loss: {train_loss/len(train_loader):.4f}, Train Acc: {train_acc:.2f}%, Val Loss: {val_loss/len(val_loader):.4f}, Val Acc: {val_acc:.2f}%')
        
        # Save best model
        if val_acc > best_val_acc:
            best_val_acc = val_acc
            torch.save(classifier.state_dict(), "custom_behavior_classifier_best.pt")
            print(f"New best model saved! Val Acc: {val_acc:.2f}%")
        
        scheduler.step()
    
    print(f"\nTraining completed! Best validation accuracy: {best_val_acc:.2f}%")
    
    # Save final model and class mapping
    torch.save(classifier.state_dict(), "custom_behavior_classifier_final.pt")
    
    # Save class mapping
    with open("custom_behavior_classes.json", "w") as f:
        json.dump(BEHAVIOR_CLASSES, f, indent=2)
    
    print("Models and class mapping saved!")

def test_custom_classifier():
    """Test the trained classifier"""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    
    # Load models
    encoder = load_pretrained_vjepa_encoder().to(device)
    classifier = create_custom_classifier().to(device)
    classifier.load_state_dict(torch.load("custom_behavior_classifier_best.pt"))
    classifier.eval()
    
    # Load class mapping
    with open("custom_behavior_classes.json", "r") as f:
        behavior_classes = json.load(f)
    
    print("\nTesting classifier on sample videos...")
    
    # Test on a few sample videos
    test_videos = [
        "/workspace/vjepa2/data/about_to_move_hat/IMG_0726_clean_007_visible.mp4",
        "/workspace/vjepa2/data/about_to_move_knife/IMG_0726_clean_004_visible.mp4"
    ]
    
    for video_path in test_videos:
        if os.path.exists(video_path):
            # Load and process video
            vr = VideoReader(video_path)
            frame_idx = np.arange(0, min(len(vr), 128), 2)
            video = vr.get_batch(frame_idx).asnumpy()
            video_tensor = simple_video_transform(video).unsqueeze(0).to(device)  # Add batch dimension
            
            # Get prediction
            with torch.no_grad():
                features = encoder(video_tensor)
                logits = classifier(features)
                probs = F.softmax(logits, dim=1)
                predicted_class = torch.argmax(probs, dim=1).item()
                confidence = probs[0][predicted_class].item() * 100
            
            video_name = os.path.basename(video_path)
            predicted_behavior = behavior_classes[str(predicted_class)]
            print(f"{video_name}: {predicted_behavior} ({confidence:.2f}%)")

if __name__ == "__main__":
    # Run training
    train_custom_classifier()
    
    # Test the trained model
    test_custom_classifier()
