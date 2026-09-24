"""
Renders paper5 diagrams and tables (HTML/SVG) to tight PNGs using headless
Chrome. Each target element is written to its own standalone HTML sized to the
content, so a full-page screenshot is exactly that element with no padding.
"""
import re
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).parent
FIG = ROOT / "figures"
FIG.mkdir(exist_ok=True)
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

# (source html, element id, output png)
TARGETS = [
    ("diagrams.html", "pipeline", "diag_pipeline.png"),
    
    
]


def extract_head(html):
    m = re.search(r"<head>(.*?)</head>", html, re.S)
    return m.group(1) if m else ""


def extract_element(html, el_id):
    m = re.search(r'<(\w+)[^>]*\bid=["\']' + re.escape(el_id) + r'["\']', html)
    if not m:
        raise SystemExit(f"element id={el_id} not found")
    tag = m.group(1)
    start = m.start()
    depth = 0
    pos = start
    open_re = re.compile(r"<" + tag + r"\b", re.I)
    close_re = re.compile(r"</" + tag + r">", re.I)
    idx = start
    while idx < len(html):
        o = open_re.search(html, idx)
        c = close_re.search(html, idx)
        if c is None:
            break
        if o is not None and o.start() < c.start():
            depth += 1
            idx = o.end()
        else:
            depth -= 1
            idx = c.end()
            if depth == 0:
                return html[start:idx]
    raise SystemExit(f"could not close element {el_id}")


def render(src, el_id, out_png):
    html = (ROOT / src).read_text()
    head = extract_head(html)
    el = extract_element(html, el_id)
    page = (f"<!doctype html><html><head>{head}"
            "<style>html,body{margin:0;padding:0;background:#fff}"
            "body{display:inline-block}</style></head>"
            f"<body>{el}</body></html>")
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=ROOT, delete=False) as f:
        f.write(page)
        tmp = Path(f.name)
    try:
        subprocess.run([
            CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
            "--force-device-scale-factor=3", "--default-background-color=FFFFFFFF",
            "--window-size=1500,1300",
            f"--screenshot={FIG / out_png}", f"file://{tmp}",
        ], check=True, capture_output=True, timeout=60)
        subprocess.run([
            "magick", str(FIG / out_png), "-trim", "+repage",
            "-bordercolor", "white", "-border", "16", str(FIG / out_png),
        ], check=True, capture_output=True, timeout=60)
        print(" wrote", out_png)
    finally:
        tmp.unlink(missing_ok=True)


if __name__ == "__main__":
    for src, el_id, out in TARGETS:
        render(src, el_id, out)
    print("Done. Figures in", FIG)
