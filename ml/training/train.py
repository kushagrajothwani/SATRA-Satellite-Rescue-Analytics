"""Baseline U-Net training loop for SAR flood segmentation.

Usage:
    python -m ml.training.train --data ml/datasets/kuro_siwo --epochs 20 \
        --out ml/models/unet_sar.pt

This script is a *runnable baseline*. It expects a dataset laid out as:
    <data>/tiles/*.npy   -> float32 array (C, H, W)
    <data>/masks/*.npy   -> uint8 array  (H, W) with classes 0/1/2

Adapt the Dataset class to your downloaded dataset format. Never report
performance you did not measure.
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--epochs", type=int, default=20)
    ap.add_argument("--batch", type=int, default=8)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--out", default="ml/models/unet_sar.pt")
    ap.add_argument("--channels", type=int, default=6)
    ap.add_argument("--classes", type=int, default=3)
    args = ap.parse_args()

    try:
        import numpy as np
        import torch
        from torch.utils.data import DataLoader, Dataset
    except Exception:
        raise SystemExit(
            "PyTorch/NumPy are required for training. Install with:\n"
            "  pip install torch --index-url https://download.pytorch.org/whl/cpu"
        )

    from ml.models.unet import build_unet, dice_loss, iou_score

    data_dir = Path(args.data)

    class FloodTiles(Dataset):
        def __init__(self, tiles_dir: Path, masks_dir: Path):
            self.tiles = sorted(tiles_dir.glob("*.npy"))
            self.masks_dir = masks_dir

        def __len__(self):
            return len(self.tiles)

        def __getitem__(self, i):
            t = np.load(self.tiles[i]).astype("float32")
            m = np.load(self.masks_dir / self.tiles[i].name).astype("int64")
            return torch.from_numpy(t), torch.from_numpy(m)

    tiles_dir = data_dir / "tiles"
    masks_dir = data_dir / "masks"
    if not tiles_dir.exists():
        raise SystemExit(f"No tiles found at {tiles_dir}. Prepare the dataset first.")

    ds = FloodTiles(tiles_dir, masks_dir)
    # NOTE: for real work, split by EVENT/GEOGRAPHY, not randomly by tile.
    n_val = max(1, int(0.2 * len(ds)))
    train_ds, val_ds = torch.utils.data.random_split(ds, [len(ds) - n_val, n_val])
    train_dl = DataLoader(train_ds, batch_size=args.batch, shuffle=True)
    val_dl = DataLoader(val_ds, batch_size=args.batch)

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = build_unet(args.channels, args.classes).to(device)
    opt = torch.optim.Adam(model.parameters(), lr=args.lr)
    ce = torch.nn.CrossEntropyLoss()

    best_iou = 0.0
    for epoch in range(1, args.epochs + 1):
        model.train()
        total = 0.0
        for x, y in train_dl:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            logits = model(x)
            loss = ce(logits, y) + dice_loss(logits, y)
            loss.backward()
            opt.step()
            total += loss.item()
        print(f"epoch {epoch}: train_loss={total / max(1, len(train_dl)):.4f}")

        model.eval()
        ious = []
        with torch.no_grad():
            for x, y in val_dl:
                x, y = x.to(device), y.to(device)
                pred = model(x).argmax(1)
                ious.append(iou_score(pred, y, args.classes))
        val_iou = sum(ious) / len(ious) if ious else 0.0
        print(f"          val_IoU={val_iou:.4f}")
        if val_iou >= best_iou:
            best_iou = val_iou
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), args.out)

    print(f"Best validation IoU: {best_iou:.4f}  (saved to {args.out})")


if __name__ == "__main__":
    main()
