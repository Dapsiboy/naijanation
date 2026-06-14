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

function makeCard(item) {
  const a = link(item.url, "card");
  const grad = sourceGradient(item.source);

  let imgHtml = "";
  if (item.image) {
    imgHtml = `
      <div class="card-img" style="background:${grad}">
        <img src="${item.image}" alt="" loading="lazy"
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
        <span class="time">${timeAgo(item.published)}</span>
      </div>
      <div class="card-title">${item.title}</div>
      ${item.summary ? `<div class="card-summary">${item.summary}</div>` : ""}
    </div>
  `;
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

function fillGoogleTrends(trends) {
  const list = document.getElementById("google-trends");
  list.innerHTML = "";
  if (!trends?.length) { list.appendChild(el("li", "empty", "No trend data available.")); return; }
  trends.forEach(topic => list.appendChild(el("li", null, topic)));
}

function fillReddit(items) {
  const box = document.getElementById("reddit-list");
  box.innerHTML = "";
  if (!items?.length) { box.appendChild(el("div", "empty", "No Reddit posts available.")); return; }
  const frag = document.createDocumentFragment();
  items.forEach(item => {
    const div = el("div", "trend-item");
    div.innerHTML = `
      <a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.title}</a>
      <div class="trend-sub">r/${item.subreddit} &middot; ${item.upvotes.toLocaleString()} upvotes</div>
    `;
    frag.appendChild(div);
  });
  box.appendChild(frag);
}

function fillYoutube(items) {
  const box = document.getElementById("youtube-list");
  box.innerHTML = "";
  if (!items?.length) {
    box.appendChild(el("div", "empty", "YouTube data not available — add a YOUTUBE_API_KEY secret to enable it."));
    return;
  }
  const frag = document.createDocumentFragment();
  items.forEach(item => {
    const div = el("div", "yt-item");
    div.innerHTML = `
      ${item.thumbnail ? `<img class="yt-thumb" src="${item.thumbnail}" alt="" loading="lazy" />` : ""}
      <div class="yt-info">
        <a href="${item.url}" target="_blank" rel="noopener noreferrer">${item.title}</a>
        <div class="yt-channel">${item.channel}</div>
      </div>
    `;
    frag.appendChild(div);
  });
  box.appendChild(frag);
}

// ─── Live TV ──────────────────────────────────────────────────────────────────

function watchTV(url) {
  window.open(url, "_blank", "noopener,noreferrer");
}

// ─── Countdown ────────────────────────────────────────────────────────────────

function startCountdown(nextIso) {
  const el = document.getElementById("next-update");
  (function tick() {
    const diff = new Date(nextIso).getTime() - Date.now();
    if (diff <= 0) { el.textContent = "Updating soon…"; return; }
    const h = Math.floor(diff / 3_600_000);
    const m = Math.floor((diff % 3_600_000) / 60_000);
    const s = Math.floor((diff % 60_000) / 1_000);
    el.textContent = `Next update in ${h}h ${String(m).padStart(2,"0")}m ${String(s).padStart(2,"0")}s`;
    setTimeout(tick, 1000);
  })();
}

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
    startCountdown(data.next_update);

    fillGrid("news-grid",     data.general_news,  "No general headlines available.");
    fillGrid("tech-grid",     data.tech_news,      "No tech headlines available.");
    fillGrid("football-grid", data.football_news,  "No football news available.");
    fillGrid("finance-grid",  data.finance_news,   "No finance news available.");
    fillEvents(data.events);

    const wc = data.worldcup || {};
    fillFixtures(wc.fixtures);
    fillGrid("wc-grid", wc.news, "No World Cup news available.");

    const t = data.trending || {};
    fillGoogleTrends(t.google_trends);
    fillReddit(t.reddit);
    fillYoutube(t.youtube);

  } catch (err) {
    console.error("Failed to load headlines:", err);
    document.getElementById("news-grid").innerHTML =
      `<div class="empty">Could not load headlines — please refresh or check back soon.</div>`;
  }
}

load();

// Auto-reload when next update arrives
fetch(`${DATA_URL}?t=${Date.now()}`)
  .then(r => r.json())
  .then(d => {
    const delay = new Date(d.next_update).getTime() - Date.now() + 30_000;
    if (delay > 0) setTimeout(() => location.reload(), delay);
  })
  .catch(() => {});
