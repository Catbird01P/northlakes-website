#!/usr/bin/env python3
"""Publish the next queued blog post.

Reads _queue/queue.json (ordered list), moves the first unpublished post from
_queue/ into blog/, stamps today's date into its JSON-LD, adds a card to the top
of blog/index.html and a <url> to sitemap.xml, then records it in
_queue/published.json. Only publishes once per Chicago calendar day, and only
at/after 9:00 AM Chicago, unless --force is passed.

Exit codes: 0 = published or nothing to do (prints reason).
"""
import html, json, re, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent.parent
QUEUE_DIR = ROOT / "_queue"
QUEUE = QUEUE_DIR / "queue.json"
LOG = QUEUE_DIR / "published.json"
BLOG = ROOT / "blog"
INDEX = BLOG / "index.html"
SITEMAP = ROOT / "sitemap.xml"
SITE = "https://northlakescopacking.com"
PUBLISH_HOUR = 9

CARD = """    <div style="background:#fff;border:1px solid #E4E0D6;border-radius:10px;padding:1.5rem;display:flex;flex-direction:column;">
      <span style="font-size:0.62rem;font-weight:700;letter-spacing:0.14em;text-transform:uppercase;color:#A8322D;display:block;margin-bottom:0.5rem">{category}</span>
      <h3 style="font-size:0.95rem;font-weight:800;color:#1E2622;margin-bottom:0.4rem;line-height:1.4;flex:1"><a href="/blog/{file}" style="color:#1E2622;text-decoration:none">{title}</a></h3>
      <p style="font-size:0.85rem;color:#59625D;margin-bottom:0.75rem;line-height:1.6">{excerpt}</p>
      <a href="/blog/{file}" style="font-size:0.78rem;font-weight:700;color:#A8322D;text-decoration:none">Read &rarr;</a>
    </div>
"""


def meta(page, pattern):
    m = re.search(pattern, page, re.I | re.S)
    return html.unescape(m.group(1)).strip() if m else None


def out(key, value):
    print(f"{key}={value}")
    gh = __import__("os").environ.get("GITHUB_OUTPUT")
    if gh:
        with open(gh, "a") as f:
            f.write(f"{key}={value}\n")


def main():
    force = "--force" in sys.argv
    now = datetime.now(ZoneInfo("America/Chicago"))
    today = now.strftime("%Y-%m-%d")

    queue = json.loads(QUEUE.read_text())
    log = json.loads(LOG.read_text()) if LOG.exists() else []
    done = {e["file"] for e in log}

    if not force:
        if now.hour < PUBLISH_HOUR:
            out("published", ""); print(f"Too early ({now:%H:%M} CT)."); return
        if any(e["date"] == today for e in log):
            out("published", ""); print(f"Already published today ({today})."); return

    pending = [q for q in queue if q["file"] not in done]
    if not pending:
        out("published", ""); print("Queue empty."); return
    item = pending[0]
    fname = item["file"]
    src, dst = QUEUE_DIR / fname, BLOG / fname
    if not src.exists():
        sys.exit(f"Queued file missing: {src}")
    if dst.exists():
        sys.exit(f"Refusing to overwrite existing post: {dst}")

    page = src.read_text()
    title = item.get("title") or meta(page, r'property="og:title"\s+content="([^"]+)"') \
        or re.sub(r"\s*\|.*$", "", meta(page, r"<title>(.*?)</title>") or fname)
    excerpt = item.get("excerpt") or meta(page, r'name="description"\s+content="([^"]+)"') or ""
    category = item.get("category", "Journal")

    # Stamp publish date into JSON-LD
    page = re.sub(r'"datePublished":"[^"]*"', f'"datePublished":"{today}"', page)
    page = re.sub(r'"dateModified":"[^"]*"', f'"dateModified":"{today}"', page)
    dst.write_text(page)
    src.unlink()

    # Card at top of the Journal grid
    idx = INDEX.read_text()
    marker = '<div class="post-grid">\n'
    if marker not in idx:
        sys.exit("Could not find post-grid in blog/index.html")
    card = CARD.format(category=html.escape(category), file=fname,
                       title=html.escape(title, quote=False), excerpt=html.escape(excerpt, quote=False))
    INDEX.write_text(idx.replace(marker, marker + card, 1))

    # Sitemap entry + bump /blog/ lastmod
    sm = SITEMAP.read_text()
    loc = f"{SITE}/blog/{fname}"
    if loc not in sm:
        sm = sm.replace("</urlset>", f"  <url><loc>{loc}</loc><lastmod>{today}</lastmod><priority>0.8</priority></url>\n</urlset>")
    sm = re.sub(r"(<loc>https://northlakescopacking\.com/blog/</loc><lastmod>)[^<]*", rf"\g<1>{today}", sm)
    SITEMAP.write_text(sm)

    log.append({"file": fname, "date": today, "title": title})
    LOG.write_text(json.dumps(log, indent=2) + "\n")
    out("published", fname)
    out("remaining", len(pending) - 1)
    print(f"Published {fname} ({title}). {len(pending) - 1} left in queue.")


if __name__ == "__main__":
    main()
