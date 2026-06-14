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

WORLDCUP_FEEDS = {
    "BBC Sport WC":    "https://feeds.bbci.co.uk/sport/football/world-cup/rss.xml",
    "Sky Sports":      "https://www.skysports.com/rss/12040",
    "Goal.com":        "https://www.goal.com/feeds/en/news",
    "ESPN Soccer":     "https://www.espn.com/espn/rss/soccer/news",
    "AP Sports":       "https://apnews.com/sports/rss",
    "Completesports":  "https://www.completesports.com/feed/",
    "Brila FM":        "https://www.brilafm.com/feed/",
    "Marca (English)": "https://www.marca.com/en/rss/world_cup.xml",
}

WC_KEYWORDS = [
    "world cup", "fifa 2026", "wc2026", "wc 2026", "group stage",
    "knockout", "quarter-final", "semi-final", "golden boot",
    "world cup 2026", "canada mexico usa", "usa 2026", "super eagles wc",
    "round of 16", "group a", "group b", "group c", "group d",
    "group e", "group f", "group g", "group h",
]

FINANCE_FEEDS = {
    "Nairametrics Markets":  "https://nairametrics.com/category/stock-market-2/feed/",
    "BusinessDay Markets":   "https://businessday.ng/markets/feed/",
    "BusinessDay Finance":   "https://businessday.ng/finance/feed/",
    "Punch Business":        "https://punchng.com/category/business/feed/",
    "The Cable Business":    "https://www.thecable.ng/category/business/feed",
    "MarketWatch":           "https://feeds.marketwatch.com/marketwatch/topstories/",
    "Yahoo Finance":         "https://finance.yahoo.com/news/rssindex",
    "Investopedia":          "https://www.investopedia.com/feedbuilder/feed/getfeed?feedName=rss_headline",
    "Reuters Business":      "https://feeds.reuters.com/reuters/businessNews",
    "Bloomberg Markets":     "https://feeds.bloomberg.com/markets/news.rss",
}

FOOTBALL_FEEDS = {
    "Completesports": "https://www.completesports.com/feed/",
    "Brila FM": "https://www.brilafm.com/feed/",
    "SportingLife NG": "https://www.sportinglife.ng/feed/",
    "BBC Sport Football": "https://feeds.bbci.co.uk/sport/football/rss.xml",
    "Sky Sports Football": "https://www.skysports.com/rss/12040",
    "Goal.com": "https://www.goal.com/feeds/en/news",
    "ESPN Soccer": "https://www.espn.com/espn/rss/soccer/news",
    "SuperSport": "https://supersport.com/rss/football",
    "Punch Sports": "https://punchng.com/category/sports/football/feed/",
    "Vanguard Sports": "https://www.vanguardngr.com/category/sports/feed/",
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


def extract_image(entry):
    # media:thumbnail (most common in news feeds)
    thumbnails = getattr(entry, "media_thumbnail", None)
    if thumbnails:
        return thumbnails[0].get("url", "")

    # media:content with image type
    media = getattr(entry, "media_content", None)
    if media:
        for m in media:
            url = m.get("url", "")
            if url and ("image" in m.get("type", "") or
                        any(url.lower().endswith(e) for e in (".jpg", ".jpeg", ".png", ".webp"))):
                return url
        if media[0].get("url"):
            return media[0]["url"]

    # enclosures
    for enc in getattr(entry, "enclosures", []):
        if "image" in enc.get("type", ""):
            return enc.get("href", "") or enc.get("url", "")

    # first <img> in content or summary HTML
    for html in [
        ((entry.get("content") or [{}])[0].get("value", "")),
        entry.get("summary", ""),
    ]:
        m = re.search(r'<img[^>]+src=["\']([^"\']{10,})["\']', html, re.I)
        if m:
            url = m.group(1)
            if url.startswith("http"):
                return url

    return ""


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
                    "image": extract_image(entry),
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


def fetch_wc_fixtures():
    try:
        r = requests.get(
            "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard",
            headers={"User-Agent": UA}, timeout=10,
        )
        fixtures = []
        for event in r.json().get("events", []):
            comp = event.get("competitions", [{}])[0]
            comps = comp.get("competitors", [])
            if len(comps) < 2:
                continue
            home = next((c for c in comps if c.get("homeAway") == "home"), comps[0])
            away = next((c for c in comps if c.get("homeAway") == "away"), comps[1])
            status = comp.get("status", {})
            fixtures.append({
                "home":       home.get("team", {}).get("displayName", ""),
                "home_abbr":  home.get("team", {}).get("abbreviation", ""),
                "home_score": home.get("score", ""),
                "away":       away.get("team", {}).get("displayName", ""),
                "away_abbr":  away.get("team", {}).get("abbreviation", ""),
                "away_score": away.get("score", ""),
                "status":     status.get("type", {}).get("shortDetail", ""),
                "completed":  status.get("type", {}).get("completed", False),
                "date":       event.get("date", ""),
                "venue":      comp.get("venue", {}).get("fullName", ""),
                "url":        (event.get("links") or [{}])[0].get("href", ""),
            })
        print(f"  [OK ] WC Fixtures: {len(fixtures)} matches")
        return fixtures
    except Exception as e:
        print(f"  [ERR] WC Fixtures: {e}")
        return []


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

    print("\n── Football ──")
    football_news = []
    for name, url in FOOTBALL_FEEDS.items():
        football_news.extend(fetch_feed(name, url, limit=12))
        time.sleep(0.4)
    football_news.sort(key=lambda x: x["published"], reverse=True)
    football_news = football_news[:60]
    print(f"  [--] {len(football_news)} football articles")

    print("\n── World Cup 2026 ──")
    wc_raw = []
    for name, url in WORLDCUP_FEEDS.items():
        wc_raw.extend(fetch_feed(name, url, limit=15))
        time.sleep(0.4)
    wc_news = []
    for a in wc_raw:
        text = (a["title"] + " " + a.get("summary", "")).lower()
        if a["source"] == "BBC Sport WC" or any(kw in text for kw in WC_KEYWORDS):
            wc_news.append(a)
    wc_news.sort(key=lambda x: x["published"], reverse=True)
    wc_news = wc_news[:50]
    wc_fixtures = fetch_wc_fixtures()
    print(f"  [--] {len(wc_news)} WC articles, {len(wc_fixtures)} fixtures")

    print("\n── Finance & Stocks ──")
    finance_news = []
    for name, url in FINANCE_FEEDS.items():
        finance_news.extend(fetch_feed(name, url, limit=12))
        time.sleep(0.4)
    finance_news.sort(key=lambda x: x["published"], reverse=True)
    finance_news = finance_news[:60]
    print(f"  [--] {len(finance_news)} finance articles")

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
        "football_news": football_news,
        "worldcup": {
            "news": wc_news,
            "fixtures": wc_fixtures,
        },
        "finance_news": finance_news,
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
    print(f"  General: {len(general_news)}, Tech: {len(tech_news)}, Events: {len(events)}, Football: {len(football_news)}")
    print(f"  Google Trends: {len(google_trends)}, Reddit: {len(reddit)}, YouTube: {len(youtube)}")


if __name__ == "__main__":
    main()
