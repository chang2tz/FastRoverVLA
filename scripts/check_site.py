"""Check static asset references, anchors, replay integrity and release hashes."""

import hashlib
import json
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs/site"


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.refs, self.anchors, self.errors = set(), [], [], []

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if "id" in attrs:
            if attrs["id"] in self.ids:
                self.errors.append(f"Duplicate ID: {attrs['id']}")
            self.ids.add(attrs["id"])
        if tag == "img" and not attrs.get("alt"):
            if attrs.get("id") != "dialog-image":
                self.errors.append(f"Image without alt: {attrs.get('src')}")
        for key in ("href", "src", "data-image"):
            if key in attrs:
                ref = attrs[key]
                if ref.startswith("#"):
                    self.anchors.append(ref[1:])
                elif not urlsplit(ref).scheme:
                    self.refs.append(ref)


def main():
    page = Page()
    page.feed((SITE / "index.html").read_text(encoding="utf-8"))
    errors = page.errors
    for ref in page.refs:
        if not (SITE / unquote(urlsplit(ref).path)).is_file():
            errors.append(f"Missing asset: {ref}")
    for ref in page.anchors:
        if ref not in page.ids:
            errors.append(f"Missing anchor: {ref}")
    for dataset, count in (("orad", 636), ("rellis", 650)):
        rows = json.loads((SITE / f"data/{dataset}.json").read_text())
        assert len(rows) == count
        assert sum(row["refresh"] for row in rows) == (37 if dataset == "orad" else 31)
        for row in rows:
            assert all(len(row[key]) == 6 for key in ("gt", "full", "control"))
            if row["refresh"]:
                assert row["full"] == row["control"]
    manifest = json.loads((ROOT / "data/benchmark/provenance.json").read_text())
    for name, info in manifest["outputs"].items():
        assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == info["sha256"], name
    if errors:
        raise SystemExit("\n".join(errors))
    print(f"OK: {len(page.refs)} asset references, {len(page.anchors)} anchors, 1,286 replay windows and dataset checksums")


if __name__ == "__main__":
    main()
