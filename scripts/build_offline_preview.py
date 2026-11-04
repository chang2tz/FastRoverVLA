"""Build a standalone project-page preview with embedded assets and replay data."""

import argparse
import base64
import json
import re
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs/site"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    html = (SITE / "index.html").read_text(encoding="utf-8")
    html = re.sub(r'  <meta property="og:image"[^>]*>\n', '', html)
    html = re.sub(r'''<link\b[^>]*\bhref=["']styles\.css(?:\?[^"']*)?["'][^>]*>''',
                  lambda _: '<style>' + (SITE / "styles.css").read_text(encoding="utf-8") + '</style>', html)
    js = (SITE / "app.js").read_text(encoding="utf-8")
    data = {ds: json.loads((SITE / f"data/{ds}.json").read_text()) for ds in ("orad", "rellis")}
    js = 'window.__FASTROVER_PREVIEW__=' + json.dumps(data, separators=(",", ":")) + ';\n' + js
    html = re.sub(r'''<script\b[^>]*\bsrc=["']app\.js(?:\?[^"']*)?["'][^>]*>\s*</script>''',
                  lambda _: '<script>' + js.replace('</script', '<\\/script') + '</script>', html)
    # Run embedded script only once the body has been parsed, preserving defer semantics.
    start = html.index('<script>'); end = html.index('</script>', start) + len('</script>')
    block = html[start:end]; html = html[:start] + html[end:]
    html = html.replace('</body>', block + '\n</body>')
    # Source-PDF downloads are outgoing publication links, like the GitHub links.
    # Keep them usable when the preview HTML is opened outside the source tree.
    for pdf in set(re.findall(r'assets/[A-Za-z0-9_.-]+\.pdf', html)):
        html = html.replace(pdf, 'https://chang2tz.github.io/FastRoverVLA/' + pdf)
    assets = set(re.findall(r'assets/[A-Za-z0-9_.-]+\.(?:png|webp|svg|woff2)(?:\?v=\d+)?', html))
    for ref in sorted(assets, key=len, reverse=True):
        path = urlsplit(ref).path
        suffix = Path(path).suffix
        mime = {'.png': 'image/png', '.webp': 'image/webp', '.svg': 'image/svg+xml', '.woff2': 'font/woff2'}[suffix]
        value = base64.b64encode((SITE / path).read_bytes()).decode()
        html = html.replace(ref, f'data:{mime};base64,{value}')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    print(f"Standalone preview: {args.output.name} ({args.output.stat().st_size:,} bytes)")


if __name__ == "__main__":
    main()
