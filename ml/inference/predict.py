"""Inference: run the trained U-Net over a raster and write a flood mask.

Usage:
    python -m ml.inference.predict --model ml/models/unet_sar.pt \
        --input sample_data/post.tif --out sample_data/flood_prob.tif

Patchwise inference on a GeoTIFF, stitched back into a georeferenced raster.
Requires torch + rasterio + numpy.
"""
from __future__ import annotations

import argparse


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--patch", type=int, default=256)
    ap.add_argument("--channels", type=int, default=6)
    ap.add_argument("--classes", type=int, default=3)
    args = ap.parse_args()

    try:
        import numpy as np
        import rasterio
        import torch
    except Exception:
        raise SystemExit("torch + rasterio + numpy are required for inference.")

    from ml.models.unet import build_unet

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = build_unet(args.channels, args.classes).to(device)
    model.load_state_dict(torch.load(args.model, map_location=device))
    model.eval()

    with rasterio.open(args.input) as src:
        arr = src.read().astype("float32")
        profile = src.profile.copy()
        h, w = arr.shape[1], arr.shape[2]
        prob = np.zeros((args.classes, h, w), dtype="float32")
        p = args.patch
        with torch.no_grad():
            for y in range(0, h, p):
                for x in range(0, w, p):
                    tile = arr[:, y:y + p, x:x + p]
                    if tile.shape[1] < p or tile.shape[2] < p:
                        pad_h = p - tile.shape[1]
                        pad_w = p - tile.shape[2]
                        tile = np.pad(tile, ((0, 0), (0, pad_h), (0, pad_w)))
                    t = torch.from_numpy(tile[None]).to(device)
                    out = torch.softmax(model(t), dim=1)[0].cpu().numpy()
                    ph = min(p, h - y)
                    pw = min(p, w - x)
                    prob[:, y:y + ph, x:x + pw] = out[:, :ph, :pw]

        mask = prob.argmax(0).astype("uint8")
        profile.update(count=1, dtype="uint8")
        with rasterio.open(args.out, "w", **profile) as dst:
            dst.write(mask, 1)

    print(f"Wrote flood mask to {args.out}")
    print("Next: vectorise with geospatial/flood_mapping/vectorize.py")


if __name__ == "__main__":
    main()
