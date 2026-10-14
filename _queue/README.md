# Blog drip queue

Posts in this folder are NOT live. A GitHub Action (`.github/workflows/drip-blog.yml`)
moves one per day into `blog/` at 9:00 AM Central, adds its card to the Journal page and
its URL to `sitemap.xml`, and pushes — which triggers the Cloudflare build.

- Order = the order in `queue.json`. Each entry: `file` (required), `category` (card label:
  Pricing, Compliance, Fulfillment, Strategy, Packaging...), optional `title` / `excerpt`
  overrides (default: og:title and meta description from the post).
- `published.json` is the log the Action writes. Don't edit it by hand.
- Publish one immediately: GitHub → Actions → "Drip-publish blog post" → Run workflow → tick "force".
