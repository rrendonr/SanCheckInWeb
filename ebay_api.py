from flask import Flask, jsonify, request, send_from_directory
from urllib.parse import quote_plus
from typing import List

import requests
from bs4 import BeautifulSoup


app = Flask(__name__, static_folder=".", static_url_path="")


def build_ebay_sold_url(query: str) -> str:
    # Sold + completed, sort by "End Date: recent first" (_sop=13)
    q = quote_plus(query)
    return (
        "https://www.ebay.com/sch/i.html"
        f"?_nkw={q}&LH_Sold=1&LH_Complete=1&_sop=13&_ipg=60"
    )


def extract_item_urls(html: str, max_items: int = 3) -> List[str]:
    soup = BeautifulSoup(html, "html.parser")
    urls = []
    seen = set()

    # eBay uses <a> tags with /itm/ for item pages
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if "/itm/" not in href:
            continue
        if "ebay.com/itm/" not in href:
            continue
        # Clean tracking parameters to keep URL readable
        base = href.split("?")[0]
        if base in seen:
            continue
        seen.add(base)
        urls.append(href)
        if len(urls) >= max_items:
            break
    return urls


@app.route("/api/ebay-sold")
def ebay_sold():
    query = request.args.get("q", "").strip()
    if not query:
        return jsonify({"error": "Missing q parameter"}), 400

    url = build_ebay_sold_url(query)
    try:
        resp = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0 Safari/537.36"
                )
            },
            timeout=15,
        )
        resp.raise_for_status()
    except Exception as exc:  # pragma: no cover - simple error handling
        return jsonify({"error": str(exc), "searchUrl": url}), 502

    links = extract_item_urls(resp.text, max_items=3)
    return jsonify({"query": query, "searchUrl": url, "links": links})


@app.route("/")
def index():
    # Serve the frontend HTML from the same origin as the API
    return send_from_directory(".", "index.html")


if __name__ == "__main__":
    # Run local app + API: python ebay_api.py
    app.run(host="127.0.0.1", port=5000, debug=True)

