"""U-Net for SAR flood segmentation.

Input channels (default 6):
    0 post VV, 1 post VH, 2 pre VV, 3 pre VH, 4 VV change, 5 slope (optional)
Output: `num_classes` logits (0 background, 1 water/flood, 2 uncertain change).

This module requires PyTorch. It is imported lazily by the training/inference
scripts so the rest of SATRA runs without torch installed.
"""
from __future__ import annotations


def build_unet(in_channels: int = 6, num_classes: int = 3, base: int = 32):
    import torch
    import torch.nn as nn

    def block(cin, cout):
        return nn.Sequential(
            nn.Conv2d(cin, cout, 3, padding=1),
            nn.BatchNorm2d(cout),
            nn.ReLU(inplace=True),
            nn.Conv2d(cout, cout, 3, padding=1),
            nn.BatchNorm2d(cout),
            nn.ReLU(inplace=True),
        )

    class UNet(nn.Module):
        def __init__(self):
            super().__init__()
            self.d1 = block(in_channels, base)
            self.d2 = block(base, base * 2)
            self.d3 = block(base * 2, base * 4)
            self.d4 = block(base * 4, base * 8)
            self.pool = nn.MaxPool2d(2)
            self.bridge = block(base * 8, base * 16)

            self.u4 = nn.ConvTranspose2d(base * 16, base * 8, 2, stride=2)
            self.c4 = block(base * 16, base * 8)
            self.u3 = nn.ConvTranspose2d(base * 8, base * 4, 2, stride=2)
            self.c3 = block(base * 8, base * 4)
            self.u2 = nn.ConvTranspose2d(base * 4, base * 2, 2, stride=2)
            self.c2 = block(base * 4, base * 2)
            self.u1 = nn.ConvTranspose2d(base * 2, base, 2, stride=2)
            self.c1 = block(base * 2, base)
            self.out = nn.Conv2d(base, num_classes, 1)

        def forward(self, x):
            x1 = self.d1(x)
            x2 = self.d2(self.pool(x1))
            x3 = self.d3(self.pool(x2))
            x4 = self.d4(self.pool(x3))
            b = self.bridge(self.pool(x4))

            y = self.u4(b)
            y = self.c4(torch.cat([y, x4], dim=1))
            y = self.u3(y)
            y = self.c3(torch.cat([y, x3], dim=1))
            y = self.u2(y)
            y = self.c2(torch.cat([y, x2], dim=1))
            y = self.u1(y)
            y = self.c1(torch.cat([y, x1], dim=1))
            return self.out(y)

    return UNet()


def dice_loss(logits, targets, eps: float = 1e-6):
    import torch

    probs = torch.softmax(logits, dim=1)
    targets_1h = torch.nn.functional.one_hot(targets, num_classes=probs.shape[1])
    targets_1h = targets_1h.permute(0, 3, 1, 2).float()
    num = 2 * (probs * targets_1h).sum(dim=(0, 2, 3)) + eps
    den = probs.sum(dim=(0, 2, 3)) + targets_1h.sum(dim=(0, 2, 3)) + eps
    return 1 - (num / den).mean()


def iou_score(pred, target, num_classes: int = 3, eps: float = 1e-6):
    import torch

    ious = []
    for c in range(num_classes):
        p = (pred == c)
        t = (target == c)
        inter = (p & t).sum().item()
        union = (p | t).sum().item()
        if union > 0:
            ious.append(inter / (union + eps))
    return sum(ious) / len(ious) if ious else 0.0
