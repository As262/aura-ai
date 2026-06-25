"""
Train the NIMA aesthetic model on the AVA dataset.
=================================================

Produces ml_models/trained/aesthetic_nima.pth, which the runtime loads
automatically to switch the AestheticAssessor into LEARNED mode.

Dataset layout expected:
    AVA/
      images/                # AVA jpg images named <id>.jpg
      AVA.txt                # official AVA labels (id + 10 rating counts)

Usage:
    python training/train_aesthetic_model.py --ava /path/to/AVA --epochs 10

This is a standard NIMA setup (MobileNetV2 backbone + Earth Mover's Distance
loss over the 1..10 rating distribution). It needs a GPU for full AVA, but
runs on CPU for small subsets / smoke tests.
"""

import os
import argparse
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from torchvision import transforms
from PIL import Image
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ml_models.aesthetic_model import NIMA


class AVADataset(Dataset):
    def __init__(self, ava_dir, split='train', transform=None):
        self.images_dir = os.path.join(ava_dir, 'images')
        self.transform = transform
        self.samples = []
        with open(os.path.join(ava_dir, 'AVA.txt'), 'r') as f:
            for line in f:
                parts = line.split()
                if len(parts) < 12:
                    continue
                img_id = parts[1]
                counts = np.array([int(x) for x in parts[2:12]], dtype=np.float32)
                total = counts.sum()
                if total <= 0:
                    continue
                path = os.path.join(self.images_dir, f'{img_id}.jpg')
                if os.path.exists(path):
                    self.samples.append((path, counts / total))
        # simple deterministic split
        cut = int(len(self.samples) * 0.9)
        self.samples = self.samples[:cut] if split == 'train' else self.samples[cut:]

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, i):
        path, dist = self.samples[i]
        img = Image.open(path).convert('RGB')
        if self.transform:
            img = self.transform(img)
        return img, torch.from_numpy(dist)


def emd_loss(p_pred, p_true):
    """Earth Mover's Distance loss over the cumulative rating distributions."""
    cdf_pred = torch.cumsum(p_pred, dim=1)
    cdf_true = torch.cumsum(p_true, dim=1)
    return torch.mean(torch.sqrt(torch.mean((cdf_pred - cdf_true) ** 2, dim=1) + 1e-8))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ava', required=True, help='Path to AVA dataset root')
    ap.add_argument('--epochs', type=int, default=10)
    ap.add_argument('--batch', type=int, default=32)
    ap.add_argument('--lr', type=float, default=3e-4)
    args = ap.parse_args()

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    train_tf = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])

    ds = AVADataset(args.ava, 'train', train_tf)
    dl = DataLoader(ds, batch_size=args.batch, shuffle=True, num_workers=2)
    print(f"Training samples: {len(ds)}")

    model = NIMA(pretrained_backbone=True).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)

    for epoch in range(args.epochs):
        model.train()
        running = 0.0
        for imgs, dists in dl:
            imgs, dists = imgs.to(device), dists.to(device)
            opt.zero_grad()
            pred = model(imgs)
            loss = emd_loss(pred, dists)
            loss.backward()
            opt.step()
            running += loss.item()
        print(f"Epoch {epoch + 1}/{args.epochs}  EMD loss: {running / max(len(dl), 1):.4f}")

    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           'ml_models', 'trained')
    os.makedirs(out_dir, exist_ok=True)
    out = os.path.join(out_dir, 'aesthetic_nima.pth')
    torch.save(model.state_dict(), out)
    print(f"[OK] Saved learned aesthetic model to {out}")


if __name__ == '__main__':
    main()
