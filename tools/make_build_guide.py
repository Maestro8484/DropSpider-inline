"""Build docs/build_guide/build_guide.html: one self-contained page.

Takes docs/build_guide/build_guide.src.html and replaces every src="img:NAME"
with the CAD render docs/img/NAME.png, shrunk to 1000 px wide and embedded as
a JPEG data URI, so the page is a single file with no separate pictures.

    python tools/make_build_guide.py

Run it again after tools/regen_cad.ps1 changes any picture. Needs Pillow.
"""
import base64
import io
import os
import re

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "build_guide", "build_guide.src.html")
OUT = os.path.join(ROOT, "docs", "build_guide", "build_guide.html")
IMG = os.path.join(ROOT, "docs", "img")


def data_uri(name):
    im = Image.open(os.path.join(IMG, name + ".png")).convert("RGB")
    if im.width > 1000:
        im = im.resize((1000, round(im.height * 1000 / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def main():
    html = open(SRC, encoding="utf-8").read()
    names = sorted(set(re.findall(r'src="img:([\w-]+)"', html)))
    for n in names:
        html = html.replace(f'src="img:{n}"', f'src="{data_uri(n)}"')
    open(OUT, "w", encoding="utf-8", newline="\n").write(html)
    print(f"{len(names)} pictures embedded, {os.path.getsize(OUT) // 1024} KB: {OUT}")


if __name__ == "__main__":
    main()
