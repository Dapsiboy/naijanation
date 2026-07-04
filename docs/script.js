const DATA_URL = "data/headlines.json";

// ─── Utils ────────────────────────────────────────────────────────────────────

function timeAgo(iso) {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60)    return `${secs}s ago`;
  if (secs < 3600)  return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

function fmtDate(iso) {
  return new Date(iso).toLocaleString("en-NG", { dateStyle: "medium", timeStyle: "short" });
}

function fmtFixtureDate(iso) {
  if (!iso) return "";
  return new Date(iso).toLocaleString("en-NG", {
    weekday: "short", month: "short", day: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
}

function el(tag, cls, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html !== undefined) e.innerHTML = html;
  return e;
}

function link(href, cls, html) {
  const a = el("a", cls, html);
  a.href = href;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  return a;
}

// Deterministic gradient per source name
function sourceGradient(name) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = Math.imul(31, h) + name.charCodeAt(i) | 0;
  const hue  = Math.abs(h) % 360;
  const hue2 = (hue + 45) % 360;
  return `linear-gradient(135deg, hsl(${hue},40%,14%) 0%, hsl(${hue2},35%,20%) 100%)`;
}

// ─── Card renderer (with image) ───────────────────────────────────────────────

const SHARE_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><circle cx="18" cy="5" r="3"/><circle cx="6" cy="12" r="3"/><circle cx="18" cy="19" r="3"/><line x1="8.59" y1="13.51" x2="15.42" y2="17.49"/><line x1="15.41" y1="6.51" x2="8.59" y2="10.49"/></svg>`;
const WA_ICON = `<svg xmlns="http://www.w3.org/2000/svg" width="13" height="13" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z"/></svg>`;

function makeCard(item) {
  const a = link(item.url, "card");
  const grad = sourceGradient(item.source);

  let imgHtml = "";
  if (item.image) {
    imgHtml = `
      <div class="card-img" style="background:${grad}">
        <img src="${item.image}" alt="" loading="lazy"
             onload="var r=this.naturalWidth/this.naturalHeight;if(r>2.5||r<0.5)this.style.objectFit='contain'"
             onerror="this.parentNode.classList.add('card-img--err');this.remove()" />
        <div class="card-img-fallback">${item.source}</div>
      </div>`;
  } else {
    imgHtml = `
      <div class="card-img card-img--err" style="background:${grad}">
        <div class="card-img-fallback">${item.source}</div>
      </div>`;
  }

  a.innerHTML = `
    ${imgHtml}
    <div class="card-body">
      <div class="card-meta">
        <span class="badge" title="${item.source}">${item.source}</span>
        <div class="card-meta-right">
          <span class="time">${timeAgo(item.published)}</span>
        </div>
      </div>
      <div class="card-title">${item.title}</div>
      ${item.summary ? `<div class="card-summary">${item.summary}</div>` : ""}
    </div>
  `;

  const waBtn = document.createElement("button");
  waBtn.className = "card-wa";
  waBtn.title = "Share on WhatsApp";
  waBtn.innerHTML = WA_ICON;
  waBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    whatsAppShare(item.url, item.title);
  });

  const shareBtn = document.createElement("button");
  shareBtn.className = "card-share";
  shareBtn.title = "Share this article";
  shareBtn.innerHTML = SHARE_ICON;
  shareBtn.addEventListener("click", (e) => {
    e.preventDefault();
    e.stopPropagation();
    shareArticle(item.url, item.title);
  });

  const metaRight = a.querySelector(".card-meta-right");
  metaRight.appendChild(waBtn);
  metaRight.appendChild(shareBtn);

  return a;
}

function makeEventItem(item) {
  const a = link(item.url, "event-item");
  a.innerHTML = `
    <div class="event-title">${item.title}</div>
    <div class="event-meta">${item.source} &middot; ${timeAgo(item.published)}</div>
  `;
  return a;
}

// ─── Share ────────────────────────────────────────────────────────────────────

function whatsAppShare(url, title) {
  const text = encodeURIComponent(`${title}\n${url}\n\nVia Naija Digest Online — naijadigest.ng`);
  window.open(`https://wa.me/?text=${text}`, "_blank", "noopener");
}

function shareArticle(url, title) {
  const text = `${title} — via Naija Digest Online`;
  if (navigator.share) {
    navigator.share({ title, text, url }).catch(() => {});
  } else {
    navigator.clipboard.writeText(url)
      .then(() => showToast("Link copied!"))
      .catch(() => showToast("Could not copy link"));
  }
}

function showToast(msg) {
  let toast = document.getElementById("share-toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "share-toast";
    toast.className = "share-toast";
    document.body.appendChild(toast);
  }
  toast.textContent = msg;
  toast.classList.add("show");
  clearTimeout(toast._t);
  toast._t = setTimeout(() => toast.classList.remove("show"), 2200);
}

// ─── Grid & list fillers ──────────────────────────────────────────────────────

function fillGrid(id, items, emptyMsg) {
  const grid = document.getElementById(id);
  if (!grid) return;
  grid.innerHTML = "";
  if (!items?.length) {
    grid.appendChild(el("div", "empty", emptyMsg || "Nothing to show right now."));
    return;
  }
  const frag = document.createDocumentFragment();
  items.forEach(item => frag.appendChild(makeCard(item)));
  grid.appendChild(frag);
}

function fillEvents(items) {
  const box = document.getElementById("events-list");
  box.innerHTML = "";
  if (!items?.length) {
    box.appendChild(el("div", "empty", "No upcoming events found."));
    return;
  }
  const frag = document.createDocumentFragment();
  items.forEach(item => frag.appendChild(makeEventItem(item)));
  box.appendChild(frag);
}

// ─── World Cup fixtures ───────────────────────────────────────────────────────

function fillFixtures(fixtures) {
  const box = document.getElementById("wc-fixtures");
  box.innerHTML = "";
  if (!fixtures?.length) {
    box.appendChild(el("div", "empty", "No fixtures data available right now."));
    return;
  }
  const frag = document.createDocumentFragment();
  fixtures.forEach(f => {
    const card = f.url ? link(f.url, "fixture-card") : el("div", "fixture-card");
    const isLive    = !f.completed && f.home_score !== "";
    const isDone    = f.completed;
    const statusCls = isLive ? "fixture-status--live" : isDone ? "fixture-status--done" : "";

    card.innerHTML = `
      <div class="fixture-teams">
        <div class="fixture-team">
          <span class="fixture-name">${f.home}</span>
          <span class="fixture-score">${f.home_score !== "" ? f.home_score : "-"}</span>
        </div>
        <div class="fixture-mid">
          <span class="fixture-status ${statusCls}">${f.status || "vs"}</span>
        </div>
        <div class="fixture-team fixture-team--away">
          <span class="fixture-score">${f.away_score !== "" ? f.away_score : "-"}</span>
          <span class="fixture-name">${f.away}</span>
        </div>
      </div>
      ${f.venue ? `<div class="fixture-meta">${f.venue}</div>` : ""}
      ${f.date  ? `<div class="fixture-meta">${fmtFixtureDate(f.date)}</div>` : ""}
    `;
    frag.appendChild(card);
  });
  box.appendChild(frag);
}

// ─── Trending ─────────────────────────────────────────────────────────────────

function fillXTrending(items) {
  const box = document.getElementById("x-trending-list");
  box.innerHTML = "";
  if (!items?.length) { box.appendChild(el("div", "empty", "No X data available.")); return; }
  const frag = document.createDocumentFragment();
  items.forEach((item, i) => {
    if (item.type === "tweet") {
      const div = el("div", "yt-item");
      div.innerHTML = `
        ${item.image ? `<img class="yt-thumb" src="${item.image}" alt="" loading="lazy" />` : ""}
        <div class="yt-info">
          <a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.text}</a>
          <div class="trend-sub">${item.author}</div>
        </div>`;
      frag.appendChild(div);
    } else {
      const div = el("div", "x-trend-item");
      div.innerHTML = `
        <span class="x-trend-rank">${i + 1}</span>
        <a class="x-trend-tag" href="${item.url}" target="_blank" rel="noopener noreferrer">${item.tag}</a>`;
      frag.appendChild(div);
    }
  });
  box.appendChild(frag);
}

function fillMediaRow(id, items, titleKey, sourceKey, imageKey, emptyMsg) {
  const box = document.getElementById(id);
  box.innerHTML = "";
  if (!items?.length) { box.appendChild(el("div", "empty", emptyMsg)); return; }
  const row = el("div", "trend-scroll-row");
  items.forEach(item => {
    const a = document.createElement("a");
    a.className = "trend-media-card";
    a.href = item.url;
    a.target = "_blank";
    a.rel = "noopener noreferrer";
    const grad = sourceGradient(item[sourceKey] || "");
    const imgHtml = item[imageKey]
      ? `<img class="trend-media-img" src="${item[imageKey]}" alt="" loading="lazy" onerror="this.outerHTML='<div class=\\'trend-media-img-fallback\\' style=\\'background:${grad}\\'>${item[sourceKey] || ""}</div>'" />`
      : `<div class="trend-media-img-fallback" style="background:${grad}">${item[sourceKey] || ""}</div>`;
    a.innerHTML = `
      ${imgHtml}
      <div class="trend-media-title">${item[titleKey]}</div>
      ${item[sourceKey] ? `<div class="trend-media-source">${item[sourceKey]}</div>` : ""}`;
    row.appendChild(a);
  });
  box.appendChild(row);
}

// ─── Exchange Rates ───────────────────────────────────────────────────────────

const CURRENCIES = [
  { code: "USD", flag: "🇺🇸", name: "US Dollar" },
  { code: "GBP", flag: "🇬🇧", name: "British Pound" },
  { code: "EUR", flag: "🇪🇺", name: "Euro" },
  { code: "CAD", flag: "🇨🇦", name: "Canadian Dollar" },
  { code: "AUD", flag: "🇦🇺", name: "Australian Dollar" },
  { code: "CNY", flag: "🇨🇳", name: "Chinese Yuan" },
  { code: "JPY", flag: "🇯🇵", name: "Japanese Yen" },
  { code: "SAR", flag: "🇸🇦", name: "Saudi Riyal" },
  { code: "AED", flag: "🇦🇪", name: "UAE Dirham" },
  { code: "ZAR", flag: "🇿🇦", name: "South African Rand" },
  { code: "GHS", flag: "🇬🇭", name: "Ghanaian Cedi" },
  { code: "INR", flag: "🇮🇳", name: "Indian Rupee" },
];

async function loadRates() {
  const grid = document.getElementById("rates-grid");
  const ts   = document.getElementById("rates-timestamp");
  grid.innerHTML = `<div class="loading-pulse"></div><div class="loading-pulse"></div><div class="loading-pulse"></div><div class="loading-pulse"></div>`;

  try {
    const res  = await fetch("https://open.er-api.com/v6/latest/USD");
    const data = await res.json();
    if (data.result !== "success") throw new Error("API error");

    const ngnPerUsd = data.rates.NGN;
    grid.innerHTML = "";
    const frag = document.createDocumentFragment();

    CURRENCIES.forEach(({ code, flag, name }) => {
      const rate = data.rates[code];
      if (!rate) return;
      const ngnPer1 = code === "USD" ? ngnPerUsd : ngnPerUsd / rate;
      const card = el("div", "rate-card");
      card.innerHTML = `
        <div class="rate-flag">${flag}</div>
        <div class="rate-info">
          <div class="rate-name">${name} <span class="rate-code">${code}</span></div>
          <div class="rate-value">₦${ngnPer1.toLocaleString("en-NG", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
          <div class="rate-sub">per 1 ${code}</div>
        </div>
      `;
      frag.appendChild(card);
    });

    grid.appendChild(frag);
    ts.textContent = `Live · Updated ${new Date().toLocaleTimeString("en-NG")} · Auto-refreshes every 5 min`;
  } catch {
    grid.innerHTML = `<div class="empty">Could not load rates — check your connection and try again.</div>`;
    ts.textContent = "Failed to load";
  }
}

// ─── Crypto ───────────────────────────────────────────────────────────────────

const COINS = [
  { id: "bitcoin",      symbol: "BTC",  name: "Bitcoin",  icon: "₿",  color: "#f7931a" },
  { id: "ethereum",     symbol: "ETH",  name: "Ethereum", icon: "Ξ",  color: "#627eea" },
  { id: "tether",       symbol: "USDT", name: "Tether",   icon: "₮",  color: "#26a17b" },
  { id: "binancecoin",  symbol: "BNB",  name: "BNB",      icon: "◈",  color: "#f3ba2f" },
  { id: "solana",       symbol: "SOL",  name: "Solana",   icon: "◎",  color: "#9945ff" },
  { id: "ripple",       symbol: "XRP",  name: "XRP",      icon: "✕",  color: "#346aa9" },
  { id: "dogecoin",     symbol: "DOGE", name: "Dogecoin", icon: "Ð",  color: "#c2a633" },
  { id: "cardano",      symbol: "ADA",  name: "Cardano",  icon: "₳",  color: "#0033ad" },
  { id: "usd-coin",     symbol: "USDC", name: "USD Coin", icon: "◉",  color: "#2775ca" },
  { id: "tron",         symbol: "TRX",  name: "TRON",     icon: "◆",  color: "#ef0027" },
  { id: "litecoin",     symbol: "LTC",  name: "Litecoin", icon: "Ł",  color: "#345d9d" },
  { id: "chainlink",    symbol: "LINK", name: "Chainlink",icon: "⬡",  color: "#2a5ada" },
];

async function loadCrypto() {
  const grid = document.getElementById("crypto-grid");
  const ts   = document.getElementById("crypto-timestamp");
  grid.innerHTML = `<div class="loading-pulse"></div><div class="loading-pulse"></div><div class="loading-pulse"></div><div class="loading-pulse"></div>`;

  const ids = COINS.map(c => c.id).join(",");
  try {
    const res  = await fetch(
      `https://api.coingecko.com/api/v3/simple/price?ids=${ids}&vs_currencies=ngn,usd&include_24hr_change=true`
    );
    const data = await res.json();

    grid.innerHTML = "";
    const frag = document.createDocumentFragment();

    COINS.forEach(({ id, symbol, name, icon, color }) => {
      const coin = data[id];
      if (!coin) return;
      const ngn    = coin.ngn  || 0;
      const usd    = coin.usd  || 0;
      const change = coin.usd_24h_change || 0;
      const up     = change >= 0;

      const card = el("div", "crypto-card");
      card.innerHTML = `
        <div class="crypto-icon" style="background:${color}20;color:${color}">${icon}</div>
        <div class="crypto-info">
          <div class="crypto-name">${name} <span class="crypto-symbol">${symbol}</span></div>
          <div class="crypto-ngn">₦${ngn.toLocaleString("en-NG", { maximumFractionDigits: 2 })}</div>
          <div class="crypto-meta">
            <span class="crypto-usd">$${usd.toLocaleString("en-US", { maximumFractionDigits: 4 })}</span>
            <span class="${up ? "crypto-up" : "crypto-down"}">${up ? "▲" : "▼"} ${Math.abs(change).toFixed(2)}%</span>
          </div>
        </div>
      `;
      frag.appendChild(card);
    });

    grid.appendChild(frag);
    ts.textContent = `Live · Updated ${new Date().toLocaleTimeString("en-NG")} · Auto-refreshes every 5 min`;
  } catch {
    grid.innerHTML = `<div class="empty">Could not load crypto prices — CoinGecko may be rate-limiting. Try again shortly.</div>`;
    ts.textContent = "Failed to load";
  }
}

// ─── Live TV ──────────────────────────────────────────────────────────────────

function watchTV(url) {
  window.open(url, "_blank", "noopener,noreferrer");
}

// ─── Inline Radio Player ──────────────────────────────────────────────────────

let _radioStream = "";

function playRadio(name, freq, streamUrl) {
  const audio  = document.getElementById("radio-audio");
  const player = document.getElementById("radio-player");
  const btn    = document.getElementById("rp-play");
  const status = document.getElementById("rp-status");

  if (_radioStream === streamUrl && !audio.paused) {
    audio.pause();
    return;
  }

  audio.pause();
  audio.src    = streamUrl;
  _radioStream = streamUrl;
  audio.volume = parseFloat(document.getElementById("rp-vol").value);

  document.getElementById("rp-name").textContent = name;
  document.getElementById("rp-freq").textContent = freq;
  status.textContent = "Connecting…";
  btn.textContent = "⏸";

  player.style.display = "flex";
  document.body.classList.add("radio-playing");

  audio.play().catch(() => {
    status.textContent = "Could not connect — stream may be offline";
    btn.textContent = "▶";
  });
}

function toggleRadioPlay() {
  const audio = document.getElementById("radio-audio");
  const btn   = document.getElementById("rp-play");
  if (audio.paused) {
    audio.play();
    btn.textContent = "⏸";
  } else {
    audio.pause();
    btn.textContent = "▶";
  }
}

function stopRadio() {
  const audio = document.getElementById("radio-audio");
  audio.pause();
  audio.src = "";
  _radioStream = "";
  document.getElementById("radio-player").style.display = "none";
  document.body.classList.remove("radio-playing");
}

function setRadioVolume(val) {
  document.getElementById("radio-audio").volume = parseFloat(val);
}

(function wireRadioEvents() {
  const audio  = document.getElementById("radio-audio");
  const status = document.getElementById("rp-status");
  const btn    = document.getElementById("rp-play");
  if (!audio) return;
  audio.addEventListener("waiting", () => { status.textContent = "Buffering…"; });
  audio.addEventListener("playing", () => { status.textContent = "● Live"; });
  audio.addEventListener("pause",   () => { btn.textContent = "▶"; status.textContent = "Paused"; });
  audio.addEventListener("error",   () => { status.textContent = "Stream error — try again"; btn.textContent = "▶"; });
})();


// ─── Tabs ─────────────────────────────────────────────────────────────────────

document.querySelectorAll(".tab-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    document.getElementById(`tab-${btn.dataset.tab}`).classList.add("active");
  });
});

// ─── Load data ────────────────────────────────────────────────────────────────

async function load() {
  try {
    const res  = await fetch(`${DATA_URL}?t=${Date.now()}`);
    const data = await res.json();

    document.getElementById("last-updated").textContent = `Updated: ${fmtDate(data.last_updated)}`;

    fillGrid("nigerian-news-grid", data.general_news,  "No Nigerian headlines available.");
    fillGrid("africa-news-grid",   data.africa_news,   "No Africa news available.");
    fillGrid("world-news-grid",    data.world_news,    "No world news available.");
    fillGrid("tech-grid",      data.tech_news,       "No tech headlines available.");
    fillGrid("editorial-grid", data.editorial_news,  "No editorials available right now.");
    fillGrid("football-grid",  data.football_news,   "No football news available.");
    fillGrid("finance-grid",   data.finance_news,    "No finance news available.");
    fillEvents(data.events);

    const wc = data.worldcup || {};
    fillFixtures(wc.fixtures);
    fillGrid("wc-grid", wc.news, "No World Cup news available.");

    const t = data.trending || {};
    fillXTrending(t.x_trending);
    fillMediaRow("naija-creators-list", t.naija_creators, "title", "channel", "thumbnail", "No creator videos available.");
    fillMediaRow("youtube-list", t.youtube, "title", "channel", "thumbnail", "No YouTube data available.");
    fillMediaRow("celeb-list", data.celeb_news, "title", "source", "image", "No celebrity news available.");
    fillMediaRow("music-list", data.music_news, "title", "source", "image", "No music news available.");

  } catch (err) {
    console.error("Failed to load headlines:", err);
    document.getElementById("nigerian-news-grid").innerHTML =
      `<div class="empty">Could not load headlines — please refresh or check back soon.</div>`;
  }
}

load();
loadRates();
loadCrypto();

// Refresh rates and crypto every 5 minutes
setInterval(loadRates,  5 * 60 * 1000);
setInterval(loadCrypto, 5 * 60 * 1000);

// Auto-reload when next update arrives
fetch(`${DATA_URL}?t=${Date.now()}`)
  .then(r => r.json())
  .then(d => {
    const delay = new Date(d.next_update).getTime() - Date.now() + 30_000;
    if (delay > 0) setTimeout(() => location.reload(), delay);
  })
  .catch(() => {});
