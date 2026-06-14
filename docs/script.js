const DATA_URL = "data/headlines.json";

// ─── Utils ────────────────────────────────────────────────────────────────────

function timeAgo(iso) {
  const secs = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (secs < 60)   return `${secs}s ago`;
  if (secs < 3600) return `${Math.floor(secs / 60)}m ago`;
  if (secs < 86400) return `${Math.floor(secs / 3600)}h ago`;
  return `${Math.floor(secs / 86400)}d ago`;
}

function fmtDate(iso) {
  return new Date(iso).toLocaleString("en-NG", { dateStyle: "medium", timeStyle: "short" });
}

function el(tag, cls, html) {
  const e = document.createElement(tag);
  if (cls) e.className = cls;
  if (html) e.innerHTML = html;
  return e;
}

function link(href, cls, html) {
  const a = el("a", cls, html);
  a.href = href;
  a.target = "_blank";
  a.rel = "noopener noreferrer";
  return a;
}

// ─── Renderers ────────────────────────────────────────────────────────────────

function makeCard(item) {
  const a = link(item.url, "card");
  a.innerHTML = `
    <div class="card-meta">
      <span class="badge" title="${item.source}">${item.source}</span>
      <span class="time">${timeAgo(item.published)}</span>
    </div>
    <div class="card-title">${item.title}</div>
    ${item.summary ? `<div class="card-summary">${item.summary}</div>` : ""}
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

function fillGrid(id, items, emptyMsg) {
  const grid = document.getElementById(id);
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

function fillGoogleTrends(trends) {
  const list = document.getElementById("google-trends");
  list.innerHTML = "";
  if (!trends?.length) {
    list.appendChild(el("li", "empty", "No trend data available."));
    return;
  }
  trends.forEach(topic => {
    list.appendChild(el("li", null, topic));
  });
}

function fillReddit(items) {
  const box = document.getElementById("reddit-list");
  box.innerHTML = "";
  if (!items?.length) {
    box.appendChild(el("div", "empty", "No Reddit posts available."));
    return;
  }
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

    fillGrid("news-grid",  data.general_news, "No general headlines available.");
    fillGrid("tech-grid",  data.tech_news,    "No tech headlines available.");
    fillEvents(data.events);

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

// Reload the page automatically when the next update time arrives
fetch(`${DATA_URL}?t=${Date.now()}`)
  .then(r => r.json())
  .then(d => {
    const delay = new Date(d.next_update).getTime() - Date.now() + 30_000; // +30s buffer
    if (delay > 0) setTimeout(() => location.reload(), delay);
  })
  .catch(() => {});
