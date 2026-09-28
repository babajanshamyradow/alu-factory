"""Generate QR codes for a URL at several sizes.

Usage:
    python3 generate_qr.py
"""

import os

import qrcode
from qrcode.constants import ERROR_CORRECT_M

URL = "http://baweraluminium.com/"

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

# box_size = pixels per QR module, border = quiet-zone width in modules.
SIZES = {
    "small": {"box_size": 6, "border": 2},
    "medium": {"box_size": 10, "border": 4},
    "large": {"box_size": 20, "border": 4},
    "xlarge": {"box_size": 40, "border": 4},
}


def generate(url, box_size, border, out_path):
    qr = qrcode.QRCode(
        error_correction=ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    image.save(out_path)
    return image.size


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for name, params in SIZES.items():
        out_path = os.path.join(OUTPUT_DIR, f"qrcode_{name}.png")
        width, height = generate(URL, params["box_size"], params["border"], out_path)
        print(f"{name:8s} -> {out_path}  ({width}x{height}px)")


if __name__ == "__main__":
    main()
