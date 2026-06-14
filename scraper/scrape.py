import feedparser
import json
import os
import time
import re
from datetime import datetime, timezone, timedelta

import requests

# ─── FEEDS ────────────────────────────────────────────────────────────────────

GENERAL_FEEDS = {
    "Punch": "https://punchng.com/feed/",
    "Vanguard": "https://www.vanguardngr.com/feed/",
    "The Guardian NG": "https://guardian.ng/feed/",
    "ThisDay": "https://www.thisdaylive.com/index.php/feed/",
    "Daily Trust": "https://dailytrust.com/feed",
    "Premium Times": "https://www.premiumtimesng.com/feed",
    "The Cable": "https://www.thecable.ng/feed",
    "Sahara Reporters": "https://saharareporters.com/rss.xml",
    "Channels TV": "https://www.channelstv.com/feed/",
    "TVC News": "https://www.tvcnews.tv/feed/",
    "AIT News": "https://www.aitonline.tv/feed/",
    "BusinessDay": "https://businessday.ng/feed/",
    "Nairametrics": "https://nairametrics.com/feed/",
    "The Sun": "https://www.sunnewsonline.com/feed/",
    "The Nation": "https://thenationonlineng.net/feed/",
    "Tribune": "https://tribuneonlineng.com/feed/",
}

TECH_FEEDS = {
    "TechCabal": "https://techcabal.com/feed/",
    "Techpoint Africa": "https://techpoint.africa/feed/",
    "TechEconomy": "https://techeconomy.ng/feed/",
    "Disrupt Africa": "https://disrupt-africa.com/feed/",
    "Naijatechguide": "https://www.naijatechguide.com/feed",
    "IT Edge News": "https://itedgenews.ng/feed/",
    "Technext": "https://technext24.com/feed/",
    "BusinessDay Tech": "https://businessday.ng/technology/feed/",
    "Nairametrics Tech": "https://nairametrics.com/category/technology/feed/",
    "TechCrunch": "https://techcrunch.com/feed/",
    "The Verge": "https://www.theverge.com/rss/index.xml",
    "Hacker News": "https://hnrss.org/frontpage",
}

EVENT_KEYWORDS = [
    "seminar", "conference", "workshop", "webinar", "hackathon",
    "summit", "forum", "bootcamp", "training", "fellowship",
    "grant", "pitch", "demo day", "startup", "registration open",
    "apply now", "call for", "cohort", "accelerator", "incubator",
]

UA = "NaijaNation/1.0 (news aggregator)"

# ─── HELPERS ──────────────────────────────────────────────────────────────────

def strip_html(text):
    return re.sub(r"<[^>]+>", "", text or "").strip()


def parse_date(entry):
    for attr in ("published_parsed", "updated_parsed"):
        t = getattr(entry, attr, None)
        if t:
            try:
                return datetime(*t[:6], tzinfo=timezone.utc).isoformat()
            except Exception:
                pass
    return datetime.now(timezone.utc).isoformat()


def is_event(title, summary=""):
    text = (title + " " + summary).lower()
    return any(kw in text for kw in EVENT_KEYWORDS)


def fetch_feed(name, url, limit=15):
    try:
        d = feedparser.parse(url, agent=UA)
        items = []
        for entry in d.entries[:limit]:
            title = (entry.get("title") or "").strip()
            link = entry.get("link") or ""
            summary = strip_html(entry.get("summary") or "")[:300]
            published = parse_date(entry)
            if title and link:
                items.append({
                    "title": title,
                    "url": link,
                    "source": name,
                    "published": published,
                    "summary": summary,
                })
        print(f"  [{len(items):2d}] {name}")
        return items
    except Exception as e:
        print(f"  [ERR] {name}: {e}")
        return []


def fetch_google_trends():
    try:
        from pytrends.request import TrendReq
        pt = TrendReq(hl="en-NG", tz=60)
        df = pt.trending_searches(pn="nigeria")
        results = df[0].tolist()[:20]
        print(f"  [OK ] Google Trends: {len(results)} topics")
        return results
    except Exception as e:
        print(f"  [ERR] Google Trends: {e}")
        return []


def fetch_reddit():
    items = []
    subreddits = ["Nigeria", "naijatechguide", "Africa", "technology"]
    headers = {"User-Agent": UA}
    for sub in subreddits:
        try:
            r = requests.get(
                f"https://www.reddit.com/r/{sub}/hot.json?limit=10",
                headers=headers,
                timeout=10,
            )
            if r.status_code == 200:
                for post in r.json()["data"]["children"]:
                    d = post["data"]
                    if not d.get("stickied") and d.get("title"):
                        items.append({
                            "title": d["title"],
                            "url": f"https://reddit.com{d['permalink']}",
                            "subreddit": sub,
                            "upvotes": d.get("ups", 0),
                        })
            time.sleep(1.5)
        except Exception as e:
            print(f"  [ERR] Reddit r/{sub}: {e}")
    print(f"  [OK ] Reddit: {len(items)} posts")
    return items


def fetch_youtube_trending():
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("  [SKP] YouTube: no API key (set YOUTUBE_API_KEY secret)")
        return []
    try:
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/videos",
            params={
                "part": "snippet",
                "chart": "mostPopular",
                "regionCode": "NG",
                "maxResults": 10,
                "key": api_key,
            },
            timeout=10,
        )
        items = []
        for v in r.json().get("items", []):
            s = v["snippet"]
            items.append({
                "title": s["title"],
                "url": f"https://youtube.com/watch?v={v['id']}",
                "channel": s["channelTitle"],
                "thumbnail": s["thumbnails"]["medium"]["url"],
            })
        print(f"  [OK ] YouTube: {len(items)} videos")
        return items
    except Exception as e:
        print(f"  [ERR] YouTube: {e}")
        return []


# ─── MAIN ─────────────────────────────────────────────────────────────────────

def main():
    now = datetime.now(timezone.utc)
    next_update = now + timedelta(hours=3)

    print("── General news ──")
    general_news = []
    for name, url in GENERAL_FEEDS.items():
        general_news.extend(fetch_feed(name, url, limit=10))
        time.sleep(0.4)

    general_news.sort(key=lambda x: x["published"], reverse=True)
    general_news = general_news[:80]

    print("\n── Tech & events ──")
    tech_raw = []
    for name, url in TECH_FEEDS.items():
        tech_raw.extend(fetch_feed(name, url, limit=15))
        time.sleep(0.4)

    events = [a for a in tech_raw if is_event(a["title"], a.get("summary", ""))]
    tech_news = [a for a in tech_raw if not is_event(a["title"], a.get("summary", ""))]

    tech_news.sort(key=lambda x: x["published"], reverse=True)
    events.sort(key=lambda x: x["published"], reverse=True)
    tech_news = tech_news[:60]
    events = events[:30]

    print(f"  [--] {len(tech_news)} tech articles, {len(events)} events/seminars")

    print("\n── Trending ──")
    google_trends = fetch_google_trends()
    reddit = fetch_reddit()
    youtube = fetch_youtube_trending()

    data = {
        "last_updated": now.isoformat(),
        "next_update": next_update.isoformat(),
        "general_news": general_news,
        "tech_news": tech_news,
        "events": events,
        "trending": {
            "google_trends": google_trends,
            "reddit": reddit,
            "youtube": youtube,
        },
    }

    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/headlines.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved → docs/data/headlines.json")
    print(f"  General: {len(general_news)}, Tech: {len(tech_news)}, Events: {len(events)}")
    print(f"  Google Trends: {len(google_trends)}, Reddit: {len(reddit)}, YouTube: {len(youtube)}")


if __name__ == "__main__":
    main()
