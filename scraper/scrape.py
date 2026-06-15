import feedparser
import json
import os
import time
import re
from datetime import datetime, timezone, timedelta

import requests
from bs4 import BeautifulSoup

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

AFRICA_FEEDS = {
    "AllAfrica":         "https://allafrica.com/tools/headlines/rdf/latest/headlines.rdf",
    "The Africa Report": "https://www.theafricareport.com/feed/",
    "Daily Maverick":    "https://www.dailymaverick.co.za/feed/",
    "The East African":  "https://www.theeastafrican.co.ke/tea/rss.xml",
    "African Business":  "https://african.business/feed/",
    "Pulse Africa":      "https://www.pulse.africa/feed/",
}

WORLD_FEEDS = {
    "BBC News World":  "https://feeds.bbci.co.uk/news/world/rss.xml",
    "Reuters":         "https://feeds.reuters.com/reuters/worldNews",
    "Al Jazeera":      "https://www.aljazeera.com/xml/rss/all.xml",
    "AP News":         "https://apnews.com/hub/world-news?format=rss",
    "The Guardian":    "https://www.theguardian.com/world/rss",
    "France 24":       "https://www.france24.com/en/rss",
}

EDITORIAL_FEEDS = {
    "Punch Editorial":       "https://punchng.com/category/editorial/feed/",
    "Vanguard Opinion":      "https://www.vanguardngr.com/category/opinion/feed/",
    "Guardian NG Opinion":   "https://guardian.ng/category/opinion/feed/",
    "ThisDay Editorial":     "https://www.thisdaylive.com/category/editorial/feed/",
    "Daily Trust Opinion":   "https://dailytrust.com/category/opinion/feed",
    "Premium Times Opinion": "https://www.premiumtimesng.com/category/opinion/feed",
    "The Cable Opinion":     "https://www.thecable.ng/category/opinion/feed",
    "BusinessDay Opinion":   "https://businessday.ng/opinion/feed/",
    "The Nation Editorial":  "https://thenationonlineng.net/category/editorial/feed/",
    "Tribune Opinion":       "https://tribuneonlineng.com/category/opinion/feed/",
    "The Sun Editorial":     "https://www.sunnewsonline.com/category/editorial/feed/",
    "Nairametrics Opinion":  "https://nairametrics.com/category/opinion/feed/",
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

CELEB_FEEDS = {
    "Linda Ikeji":  "https://www.lindaikejisblog.com/feeds/posts/default?alt=rss",
    "BellaNaija":   "https://www.bellanaija.com/feed/",
    "SDK Celeb":    "http://www.stelladimokokorkus.com/feeds/posts/default?alt=rss",
    "YNaija":       "https://ynaija.com/feed/",
}

MUSIC_FEEDS = {
    "NotJustOk":    "https://www.notjustok.com/feed/",
    "Tooxclusive":  "https://www.tooxclusive.com/feed/",
    "360nobs":      "https://www.360nobs.com/feed/",
    "Jaguda":       "https://www.jaguda.com/feed/",
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


def fetch_x_data():
    import urllib.parse
    token = urllib.parse.unquote(os.environ.get("TWITTER_BEARER_TOKEN", ""))
    if token:
        try:
            r = requests.get(
                "https://api.twitter.com/2/tweets/search/recent",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "query": "Nigeria OR Naija -is:retweet lang:en",
                    "max_results": 10,
                    "tweet.fields": "text,public_metrics",
                    "expansions": "attachments.media_keys,author_id",
                    "media.fields": "url,preview_image_url,type",
                    "user.fields": "name,username",
                },
                timeout=10,
            )
            data = r.json()
            media_map = {m["media_key"]: m for m in data.get("includes", {}).get("media", [])}
            user_map = {u["id"]: u for u in data.get("includes", {}).get("users", [])}
            items = []
            for tweet in data.get("data", []):
                media_keys = tweet.get("attachments", {}).get("media_keys", [])
                image_url = ""
                for mk in media_keys:
                    m = media_map.get(mk, {})
                    if m.get("type") == "photo":
                        image_url = m.get("url", "")
                        break
                    elif m.get("preview_image_url"):
                        image_url = m.get("preview_image_url", "")
                        break
                author = user_map.get(tweet.get("author_id", ""), {})
                items.append({
                    "type": "tweet",
                    "text": tweet.get("text", "")[:200],
                    "url": f"https://x.com/i/web/status/{tweet['id']}",
                    "image": image_url,
                    "author": f"@{author.get('username', '')}" if author else "",
                })
            print(f"  [OK ] X Posts: {len(items)} tweets with media")
            return items
        except Exception as e:
            print(f"  [ERR] X Posts (Twitter API): {e} — falling back to trends")

    try:
        r = requests.get(
            "https://trends24.in/nigeria/",
            headers={"User-Agent": UA},
            timeout=10,
        )
        soup = BeautifulSoup(r.text, "html.parser")
        politics_keywords = [
            # Politicians
            "tinubu", "peter obi", "atiku", "kwankwaso", "wike", "el-rufai", "obi",
            "fubara", "shettima", "ganduje", "makinde", "sanwo-olu", "soludo",
            "obidient", "jagaban", "emilokan",
            # Parties
            "apc", "pdp", "labour party", "nnpp", "adc", "ndc", "sdp", "ypp", "apga",
            # Institutions & Government
            "inec", "efcc", "icpc", "cbn", "nass", "dss", "aso rock", "presidency",
            "senate", "house of rep", "national assembly", "supreme court", "tribunal",
            "minister", "governor", "commissioner",
            # Issues
            "election", "voting", "impeach", "recall", "corruption", "probe",
            "budget", "fuel subsidy", "naira", "forex", "tax reform", "palliative",
            "protest", "insecurity", "bandits", "boko haram", "coup", "democracy",
            "constituency", "bill", "policy", "abuja",
        ]
        all_items = []
        for a in soup.select(".trend-card__list li a")[:50]:
            tag = a.get_text(strip=True)
            if not tag:
                continue
            score = 1
            tag_lower = tag.lower()
            for kw in politics_keywords:
                if kw in tag_lower:
                    score = 2
                    break
            all_items.append((score, tag))
        all_items.sort(key=lambda x: x[0], reverse=True)
        items = [
            {
                "type": "trend",
                "tag": tag,
                "url": f"https://x.com/search?q={requests.utils.quote(tag)}&src=trend_click",
            }
            for _, tag in all_items[:25]
        ]
        print(f"  [OK ] X Trending (fallback): {len(items)} topics")
        return items
    except Exception as e:
        print(f"  [ERR] X Trending: {e}")
        return []


def fetch_naija_creators():
    api_key = os.environ.get("YOUTUBE_API_KEY")
    if not api_key:
        print("  [SKP] Naija Creators: no API key")
        return []
    try:
        r = requests.get(
            "https://www.googleapis.com/youtube/v3/search",
            params={
                "part": "snippet",
                "q": "Nigeria skit comedy creator vlog lifestyle music naija",
                "type": "video",
                "regionCode": "NG",
                "relevanceLanguage": "en",
                "order": "date",
                "maxResults": 25,
                "key": api_key,
            },
            timeout=10,
        )
        items = []
        for item in r.json().get("items", []):
            s = item.get("snippet", {})
            vid_id = item.get("id", {}).get("videoId", "")
            if vid_id:
                items.append({
                    "title": s.get("title", ""),
                    "channel": s.get("channelTitle", ""),
                    "url": f"https://www.youtube.com/watch?v={vid_id}",
                    "thumbnail": s.get("thumbnails", {}).get("medium", {}).get("url", ""),
                })
        print(f"  [OK ] Naija Creators: {len(items)} videos")
        return items
    except Exception as e:
        print(f"  [ERR] Naija Creators: {e}")
        return []


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
                "maxResults": 8,
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
    next_update = now + timedelta(hours=1)

    print("── General news ──")
    general_news = []
    for name, url in GENERAL_FEEDS.items():
        general_news.extend(fetch_feed(name, url, limit=10))
        time.sleep(0.4)

    general_news.sort(key=lambda x: x["published"], reverse=True)
    general_news = general_news[:80]

    print("\n── Africa News ──")
    africa_news = []
    for name, url in AFRICA_FEEDS.items():
        africa_news.extend(fetch_feed(name, url, limit=10))
        time.sleep(0.4)
    africa_news.sort(key=lambda x: x["published"], reverse=True)
    africa_news = africa_news[:50]
    print(f"  [--] {len(africa_news)} Africa articles")

    print("\n── World News ──")
    world_news = []
    for name, url in WORLD_FEEDS.items():
        world_news.extend(fetch_feed(name, url, limit=10))
        time.sleep(0.4)
    world_news.sort(key=lambda x: x["published"], reverse=True)
    world_news = world_news[:60]
    print(f"  [--] {len(world_news)} world articles")

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

    print("\n── Editorials ──")
    editorial_news = []
    for name, url in EDITORIAL_FEEDS.items():
        editorial_news.extend(fetch_feed(name, url, limit=8))
        time.sleep(0.4)
    editorial_news.sort(key=lambda x: x["published"], reverse=True)
    editorial_news = editorial_news[:60]
    print(f"  [--] {len(editorial_news)} editorials")

    print("\n── Finance & Stocks ──")
    finance_news = []
    for name, url in FINANCE_FEEDS.items():
        finance_news.extend(fetch_feed(name, url, limit=12))
        time.sleep(0.4)
    finance_news.sort(key=lambda x: x["published"], reverse=True)
    finance_news = finance_news[:60]
    print(f"  [--] {len(finance_news)} finance articles")

    print("\n── Celebrity Gossip ──")
    celeb_news = []
    for name, url in CELEB_FEEDS.items():
        celeb_news.extend(fetch_feed(name, url, limit=10))
        time.sleep(0.4)
    celeb_news.sort(key=lambda x: x["published"], reverse=True)
    celeb_news = celeb_news[:8]

    print("\n── Naija Music ──")
    music_news = []
    for name, url in MUSIC_FEEDS.items():
        music_news.extend(fetch_feed(name, url, limit=10))
        time.sleep(0.4)
    music_news.sort(key=lambda x: x["published"], reverse=True)
    music_news = music_news[:8]

    print("\n── Trending ──")
    x_trending = fetch_x_data()
    naija_creators = fetch_naija_creators()
    youtube = fetch_youtube_trending()

    data = {
        "last_updated": now.isoformat(),
        "next_update": next_update.isoformat(),
        "general_news": general_news,
        "africa_news": africa_news,
        "world_news": world_news,
        "tech_news": tech_news,
        "events": events,
        "football_news": football_news,
        "worldcup": {
            "news": wc_news,
            "fixtures": wc_fixtures,
        },
        "editorial_news": editorial_news,
        "finance_news": finance_news,
        "celeb_news": celeb_news,
        "music_news": music_news,
        "trending": {
            "x_trending": x_trending,
            "naija_creators": naija_creators,
            "youtube": youtube,
        },
    }

    os.makedirs("docs/data", exist_ok=True)
    with open("docs/data/headlines.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved → docs/data/headlines.json")
    print(f"  General: {len(general_news)}, Tech: {len(tech_news)}, Events: {len(events)}, Editorials: {len(editorial_news)}, Football: {len(football_news)}")
    print(f"  X Trending: {len(x_trending)}, Naija Creators: {len(naija_creators)}, YouTube: {len(youtube)}")


if __name__ == "__main__":
    main()
