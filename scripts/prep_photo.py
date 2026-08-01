"""Prep a source photo for ASCII conversion: remove background, boost local
contrast, composite onto white. Run once per photo, locally (not in CI) --
this needs rembg/opencv which aren't installed by the daily workflow.

Usage: python scripts/prep_photo.py source-photo.jpg
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


def prep(src_path: str, out_path: str = "source-prepped.png") -> None:
    src_bytes = Path(src_path).read_bytes()

    # 1. Remove background so the subject is isolated.
    cutout_bytes = remove(src_bytes)
    cutout = Image.open(__import__("io").BytesIO(cutout_bytes)).convert("RGBA")

    # 2. Composite onto pure white (transparent -> white, which maps to the
    #    blank end of the ASCII ramp later).
    white_bg = Image.new("RGBA", cutout.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(white_bg, cutout).convert("RGB")

    # 3. Boost local contrast with CLAHE so a flatly-lit face gets real
    #    highlights/shadows instead of converting to a dark, unreadable blob.
    gray = cv2.cvtColor(np.array(composited), cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    # Re-flatten anything that was pure background back to white so it maps
    # cleanly to the blank glyph in the ASCII ramp.
    alpha = np.array(cutout)[:, :, 3]
    contrasted = np.where(alpha < 10, 255, contrasted).astype(np.uint8)

    Image.fromarray(contrasted, mode="L").save(out_path)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("usage: python scripts/prep_photo.py <source-photo>")
        sys.exit(1)
    prep(sys.argv[1])
