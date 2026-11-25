// DG-UniCa website: builds header/footer and renders each page from the YAML files in /data.

const NAV = [
  ["index.html", "Home"],
  ["research.html", "Research"],
  ["people.html", "People"],
  ["seminars.html", "Seminars"],
  ["events.html", "Events"],
  ["publications.html", "Publications"],
  ["preprints.html", "Preprints"],
  ["contact.html", "Contact"],
];

const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const link = (url, text, cls = "") => url ? `<a href="${esc(url)}" target="_blank" rel="noopener" class="${cls}">${text}</a>` : text;
const initials = (name) => name.split(/\s+/).filter((w) => /^[A-ZÀ-Ý]/.test(w)).map((w) => w[0]).slice(0, 2).join("");

async function load(name) {
  const res = await fetch(`data/${name}.yml`, { cache: "no-cache" }); // always pick up edited data files
  if (!res.ok) throw new Error(`Cannot load data/${name}.yml`);
  return jsyaml.load(await res.text());
}

function parseDate(d) {
  if (d instanceof Date) return d;
  const [y, m, day] = String(d).split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, day));
}
function today() {
  const n = new Date();
  return new Date(Date.UTC(n.getFullYear(), n.getMonth(), n.getDate()));
}
const fmt = (d, opts) => d.toLocaleDateString("en-GB", { timeZone: "UTC", ...opts });

/* ---------- Layout ---------- */
function buildChrome(site) {
  let page = location.pathname.split("/").pop() || "index.html";
  if (page === "topic.html") page = "research.html";
  const header = document.createElement("header");
  header.className = "site-header";
  header.innerHTML = `
    <div class="wrap">
      <a class="brand" href="index.html">
        <span class="brand-mark"><img src="assets/img/logo.png" alt="DG-UniCa logo"></span>
        <span>${esc(site.name)}<small>Differential Geometry · ${esc(site.university)}</small></span>
      </a>
      <button class="menu-btn" aria-label="Menu">☰</button>
      <nav><ul>${NAV.map(([href, label]) => `<li><a href="${href}" class="${href === page ? "active" : ""}">${label}</a></li>`).join("")}</ul></nav>
    </div>`;
  document.body.prepend(header);
  header.querySelector(".menu-btn").onclick = () => header.querySelector("nav").classList.toggle("open");

  const footer = document.createElement("footer");
  footer.innerHTML = `
    <div class="wrap foot-right">
      <div class="foot-addr">${site.address.map((l) => l === site.university ? link(site.university_url, esc(l)) : l === site.department ? link(site.department_url, esc(l)) : esc(l)).join("<br>")}</div>
      ${link(site.department_url, `<img class="foot-logo" src="assets/img/logo-dmi.png" alt="Department of Mathematics and Computer Science (DMI)">`)}
    </div>`;
  document.body.append(footer);
}

/* ---------- Components ---------- */
// A body block: "## Title" -> heading, a list -> bullet list, "$$...$$" -> displayed formula, else paragraph.
function block(b) {
  if (Array.isArray(b)) return `<ul>${b.map((x) => `<li>${esc(x)}</li>`).join("")}</ul>`;
  const s = String(b).trim();
  if (s.startsWith("## ")) return `<h3>${esc(s.slice(3))}</h3>`;
  if (s.startsWith("$$")) return `<div class="display-math">${esc(s)}</div>`;
  return `<p>${esc(s)}</p>`;
}

const topicUrl = (t) => `topic.html?t=${encodeURIComponent(t.slug)}`;

function topicCard(t) {
  return `<a class="card topic-card" href="${topicUrl(t)}">
    <div class="topic-thumb symbol">${esc(t.icon || "•")}</div>
    <h3>${esc(t.title)}</h3><p>${esc(t.text)}</p><span class="more">Read more →</span></a>`;
}

function personCard(p) {
  const av = p.photo ? `<img src="${esc(p.photo)}" alt="">` : esc(initials(p.name));
  const meta = p.role || p.now || "";
  const inner = `<div class="avatar">${av}</div><div><div class="name">${esc(p.name)}</div>${meta ? `<div class="meta">${esc(meta)}</div>` : ""}</div>`;
  return p.url
    ? `<a class="card person" href="${esc(p.url)}" target="_blank" rel="noopener">${inner}</a>`
    : `<div class="card person">${inner}</div>`;
}

function talkRow(t, isNext = false) {
  const d = parseDate(t.date);
  const abstract = t.abstract ? `<details class="abstract"><summary>Abstract</summary>${String(t.abstract).trim().split(/\n\s*\n/).map((x) => `<p>${esc(x)}</p>`).join("")}</details>` : "";
  return `
    <div class="talk ${isNext ? "next" : ""}">
      <div class="date-box"><div class="m">${fmt(d, { month: "short" })}</div><div class="d">${fmt(d, { day: "numeric" })}</div><div class="m">${fmt(d, { year: "numeric" })}</div></div>
      <div>
        ${isNext ? `<div class="badge">Next talk</div>` : ""}
        <div class="title">${esc(t.title)}</div>
        <div class="speaker">${esc(t.speaker)}${t.affiliation ? ` · ${esc(t.affiliation)}` : ""}${t.note ? ` · ${esc(t.note)}` : ""}</div>
        ${abstract}
      </div>
    </div>`;
}

function splitTalks(sem) {
  const now = today();
  const talks = [...sem.talks].sort((a, b) => parseDate(a.date) - parseDate(b.date));
  return {
    upcoming: talks.filter((t) => parseDate(t.date) >= now),
    past: talks.filter((t) => parseDate(t.date) < now).reverse(),
  };
}

// Events grouped by year on a vertical timeline (newest year first).
function eventTimeline(events) {
  const years = [...new Set(events.map((e) => e.year ?? "—"))].sort((a, b) => (b === "—") - (a === "—") || b - a);
  return `<div class="timeline">${years.map((y) => {
    const list = events.filter((e) => (e.year ?? "—") === y);
    return `<div class="tl-year">
      <div class="tl-marker"><span class="tl-dot"></span><span class="tl-label">${esc(y)}</span><span class="tl-count">${list.length} event${list.length === 1 ? "" : "s"}</span></div>
      <div class="tl-events">${list.map((e) => `
        <${e.url ? `a href="${esc(e.url)}" target="_blank" rel="noopener"` : "div"} class="card tl-event">
          <div class="tl-title">${esc(e.title)}</div>
          ${e.place ? `<div class="tl-place">📍 ${esc(e.place)}</div>` : ""}
          ${e.url ? `<span class="tl-link">Website ↗</span>` : ""}
        </${e.url ? "a" : "div"}>`).join("")}
      </div></div>`;
  }).join("")}</div>`;
}

function pubRow(p) {
  return `<li class="pub" data-search="${esc((p.authors + " " + p.title + " " + p.journal + " " + p.year).toLowerCase())}">
    <div class="authors">${esc(p.authors)}</div>
    <div>${link(p.url, `<span class="ptitle">${esc(p.title)}</span>`)}</div>
    <div class="journal"><i>${esc(p.journal)}</i> ${esc(p.details || "")}${p.arxiv ? ` ${link(p.arxiv, `arXiv:${esc(p.arxiv.split("/abs/")[1] || "")}`, "arxiv-link")}` : ""}</div>
  </li>`;
}

/* ---------- Pages ---------- */
const pages = {
  async home(main, site) {
    const [sem, pre, vis] = await Promise.all([load("seminars"), load("preprints").catch(() => ({})), load("visitors").catch(() => ({}))]);
    const now = today();
    const visitors = (vis.visitors || []).filter((v) => (!v.from || parseDate(v.from) <= now) && (!v.until || parseDate(v.until) >= now));
    const preprints = (pre.preprints || []).slice(0, 5);
    const { upcoming } = splitTalks(sem);
    main.innerHTML = `
      <section class="hero"><div class="wrap">
        <div>
          <div class="eyebrow">${esc(site.university)}</div>
          <h1>${esc(site.tagline)}</h1>
          <p class="lead">${esc(site.intro)}</p>
          <div class="btns"><a class="btn primary" href="research.html">Our research</a><a class="btn" href="people.html">People</a></div>
        </div>
        <figure class="hero-figure" title="Helicoid ⟷ catenoid: an associated family of minimal surfaces"><canvas id="surface" aria-label="Animation: helicoid deforming into a catenoid"></canvas></figure>
      </div></section>

      <section class="block"><div class="wrap home-cols">
        <div>
          <div class="section-title"><h2>Upcoming seminars</h2><a href="seminars.html">All seminars →</a></div>
          ${upcoming.length ? upcoming.slice(0, 3).map((t, i) => talkRow(t, i === 0)).join("") : `<p class="empty">No seminars scheduled at the moment.</p>`}
          ${visitors.length ? `<div class="visitors">
            <h2>Visitors</h2>
            <p class="preprints-sub">Currently visiting the group</p>
            <ul>${visitors.map((v) => `<li>
              <span class="avatar">${esc(initials(v.name))}</span>
              <div><div class="vname">${link(v.url, esc(v.name))}</div>
              <div class="vaff">${esc(v.affiliation || "")}${v.until ? ` · until ${parseDate(v.until).toLocaleDateString("en-GB", { day: "numeric", month: "short" })}` : ""}</div></div>
            </li>`).join("")}</ul>
          </div>` : ""}
        </div>
        ${preprints.length ? `<aside class="preprints">
          <div class="section-title"><h2>New on arXiv</h2><a href="preprints.html">All →</a></div>
          <p class="preprints-sub">Recent preprints by members of the group</p>
          <ul>${preprints.map((p) => `<li>
            ${link(p.url, `<span class="ptitle">${esc(p.title)}</span>`)}
            <div class="authors">${esc(p.authors)}</div>
            <div class="pdate">arXiv:${esc(p.url.split("/abs/")[1] || "")} · ${parseDate(p.date).toLocaleDateString("en-GB", { month: "short", year: "numeric" })}</div>
          </li>`).join("")}</ul>
        </aside>` : ""}
      </div></section>`;
    drawSurface(document.getElementById("surface"));
  },

  async research(main, site) {
    const research = await load("research");
    main.innerHTML = `
      <section class="page-head"><div class="wrap"><h1>Research</h1>
        <p>Our main lines of research. Choose a topic to read more about it, see who works on it and find related papers.</p></div></section>
      <section class="block"><div class="wrap"><div class="grid cols-3">${research.map(topicCard).join("")}</div></div></section>
      ${site.opportunities ? `
      <section class="block" id="opportunities"><div class="wrap">
        <h2>Opportunities for students</h2>
        <p class="section-intro">Interested in writing a thesis or a PhD in differential geometry? Here are some possible topics: get in touch with any member of the group.</p>
        <div class="two-col">
          <div class="card"><h3>Possible Master's theses</h3><ul class="topics-list">${site.opportunities.master.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>
          <div class="card"><h3>Possible PhD projects</h3><ul class="topics-list">${site.opportunities.phd.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>
        </div>
      </div></section>` : ""}`;
  },

  async topic(main) {
    const [research, people, pubs] = await Promise.all([load("research"), load("people"), load("publications")]);
    const slug = new URLSearchParams(location.search).get("t");
    const i = research.findIndex((t) => t.slug === slug);
    if (i < 0) { location.replace("research.html"); return; }
    const t = research[i];
    document.title = `${t.title} · DG-UniCa`;
    const everyone = [...people.faculty, ...people.junior];
    const members = (t.people || []).map((n) => everyone.find((p) => p.name === n) || { name: n });
    const related = pubs.filter((p) => (p.topics || []).includes(t.slug));
    const prev = research[(i - 1 + research.length) % research.length], next = research[(i + 1) % research.length];
    main.innerHTML = `
      <section class="page-head"><div class="wrap">
        <div class="crumbs"><a href="research.html">Research</a> / ${esc(t.title)}</div>
        <h1>${esc(t.title)}</h1><p>${esc(t.text)}</p>
      </div></section>
      <section class="block"><div class="wrap topic-layout">
        <article class="prose">${(t.body || []).map(block).join("")}
          ${t.reading?.length ? `<h3>Further reading</h3><ul>${t.reading.map((r) => `<li>${link(r.url, esc(r.text))}</li>`).join("")}</ul>` : ""}
        </article>
        ${t.figures?.length ? `<aside class="figures">${t.figures.map((f) => `<figure><img src="${esc(f.src)}" alt="${esc(f.caption)}" loading="lazy"><figcaption>${esc(f.caption)}</figcaption></figure>`).join("")}</aside>` : ""}
      </div></section>
      ${members.length ? `<section class="block"><div class="wrap"><h2>People</h2><div class="grid cols-4">${members.map(personCard).join("")}</div></div></section>` : ""}
      ${related.length ? `<section class="block"><div class="wrap"><div class="section-title"><h2>Recent publications</h2>${related.length > 6 ? `<a href="publications.html?topic=${encodeURIComponent(t.slug)}">All ${related.length} papers →</a>` : ""}</div><ul class="list">${related.slice(0, 6).map(pubRow).join("")}</ul></div></section>` : ""}
      <section class="block"><div class="wrap topic-nav">
        <a class="card" href="${topicUrl(prev)}"><span class="meta">← Previous</span><br>${esc(prev.title)}</a>
        <a class="card" href="${topicUrl(next)}" style="text-align:right"><span class="meta">Next →</span><br>${esc(next.title)}</a>
      </div></section>`;
  },

  async people(main) {
    const p = await load("people");
    main.innerHTML = `
      <section class="page-head"><div class="wrap"><h1>People</h1><p>Faculty and PhD students of the group.</p></div></section>
      <section class="block"><div class="wrap"><h2>Faculty</h2><div class="grid cols-4">${p.faculty.map(personCard).join("")}</div></div></section>
      <section class="block"><div class="wrap"><h2>PhD students</h2><div class="grid cols-4">${p.junior.map(personCard).join("")}</div></div></section>
      ${p.show_alumni && p.alumni?.length ? `<section class="block"><div class="wrap"><h2>Alumni</h2><div class="grid cols-3">${p.alumni.map(personCard).join("")}</div></div></section>` : ""}
      ${p.show_former && p.former?.length ? `<section class="block"><div class="wrap"><h2>Former members</h2><div class="chips">${p.former.map((x) => x.url ? link(x.url, esc(x.name), "chip") : `<span class="chip">${esc(x.name)}</span>`).join("")}</div></div></section>` : ""}`;
  },

  async seminars(main) {
    const sem = await load("seminars");
    const { upcoming, past } = splitTalks(sem);
    main.innerHTML = `
      <section class="page-head"><div class="wrap"><h1>Seminars</h1><p>${esc(sem.title)}: research talks in geometry, algebra and logic, open to everyone.</p></div></section>
      <section class="block"><div class="wrap">
        <div class="info-bar"><span><b>When</b> ${esc(sem.schedule)}</span><span><b>Where</b> ${esc(sem.room)}, Department of Mathematics and Computer Science</span></div>
        <h2>Upcoming</h2>
        ${upcoming.length ? upcoming.map((t, i) => talkRow(t, i === 0)).join("") : `<p class="empty">No seminars scheduled at the moment.</p>`}
      </div></section>
      <section class="block past"><div class="wrap">
        <h2>Past talks</h2>
        ${past.map((t) => talkRow(t)).join("") || `<p class="empty">None yet.</p>`}
        <p style="margin-top:20px">${link(sem.past_editions_url, "Past editions of the seminar →")}</p>
      </div></section>`;
  },

  async events(main) {
    const events = await load("events");
    main.innerHTML = `
      <section class="page-head"><div class="wrap"><h1>Events</h1><p>Conferences and workshops organised or co-organised by members of the group in the last decade.</p></div></section>
      <section class="block"><div class="wrap">${eventTimeline(events)}</div></section>`;
  },

  async preprints(main) {
    const pre = await load("preprints");
    const items = pre.preprints || [];
    const year = (p) => String(p.date).slice(0, 4);
    const years = [...new Set(items.map(year))];
    const row = (p) => `<li class="pub" data-search="${esc((p.authors + " " + p.title).toLowerCase())}">
      <div class="authors">${esc(p.authors)}</div>
      <div>${link(p.url, `<span class="ptitle">${esc(p.title)}</span>`)}</div>
      <div class="journal">${link(p.url, `arXiv:${esc(p.url.split("/abs/")[1] || "")}`, "arxiv-link")} <span class="pdate-inline">submitted ${parseDate(p.date).toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric" })}</span></div>
    </li>`;
    main.innerHTML = `
      <section class="page-head"><div class="wrap"><h1>Preprints</h1><p>Recent preprints of members of the group on arXiv, not yet published. Published papers are listed under ${`<a href="publications.html">Publications</a>`}.</p></div></section>
      <section class="block"><div class="wrap">
        <div class="filters"><input class="search" type="search" placeholder="Filter by author or title…" aria-label="Filter preprints"></div>
        <p class="count"></p>
        ${years.map((y) => `<div class="year-group"><h2 class="year-head">${y}</h2>
          <ul class="list">${items.filter((p) => year(p) === y).map(row).join("")}</ul></div>`).join("") || `<p class="empty">No preprints at the moment.</p>`}
      </div></section>`;
    const q = main.querySelector("input.search"), count = main.querySelector(".count");
    const apply = () => {
      const text = q.value.toLowerCase().trim();
      let n = 0;
      main.querySelectorAll(".year-group").forEach((g) => {
        let shown = 0;
        g.querySelectorAll("li").forEach((li) => { const ok = li.dataset.search.includes(text); li.style.display = ok ? "" : "none"; shown += ok; });
        g.style.display = shown ? "" : "none"; n += shown;
      });
      count.textContent = `${n} preprint${n === 1 ? "" : "s"}`;
    };
    q.addEventListener("input", apply); apply();
  },

  async publications(main) {
    const [pubs, research] = await Promise.all([load("publications"), load("research")]);
    const years = [...new Set(pubs.map((p) => p.year))].sort((a, b) => b - a);
    const initial = new URLSearchParams(location.search).get("topic") || "";
    main.innerHTML = `
      <section class="page-head"><div class="wrap"><h1>Publications</h1><p>All publications of members of the group since 2000, collected from zbMATH Open.</p></div></section>
      <section class="block"><div class="wrap">
        <div class="filters">
          <input class="search" type="search" placeholder="Filter by author, title, journal…" aria-label="Filter publications">
          <select class="search topic-filter" aria-label="Filter by research topic">
            <option value="">All topics</option>
            ${research.map((t) => `<option value="${esc(t.slug)}" ${t.slug === initial ? "selected" : ""}>${esc(t.title)}</option>`).join("")}
          </select>
          <select class="search year-filter" aria-label="Filter by year">
            <option value="">All years</option>
            ${years.map((y) => `<option value="${y}">${y}</option>`).join("")}
          </select>
        </div>
        <p class="count"></p>
        <div id="pubs">${years.map((y) => `
          <div class="year-group" data-year="${y}"><h2 class="year-head">${y}</h2>
          <ul class="list">${pubs.filter((p) => p.year === y).map((p) => pubRow(p).replace("<li ", `<li data-topics="${esc((p.topics || []).join(" "))}" `)).join("")}</ul></div>`).join("")}
        </div>
      </div></section>`;
    const q = main.querySelector('input.search'), sel = main.querySelector(".topic-filter"), ysel = main.querySelector(".year-filter"), count = main.querySelector(".count");
    const apply = () => {
      const text = q.value.toLowerCase().trim(), topic = sel.value, year = ysel.value;
      let n = 0;
      main.querySelectorAll(".year-group").forEach((g) => {
        let shown = 0;
        if (year && g.dataset.year !== year) { g.style.display = "none"; return; }
        g.querySelectorAll("li").forEach((li) => {
          const ok = li.dataset.search.includes(text) && (!topic || li.dataset.topics.split(" ").includes(topic));
          li.style.display = ok ? "" : "none"; shown += ok;
        });
        g.style.display = shown ? "" : "none"; n += shown;
      });
      count.textContent = `${n} publication${n === 1 ? "" : "s"}`;
    };
    q.addEventListener("input", apply); sel.addEventListener("change", apply); ysel.addEventListener("change", apply); apply();
  },

  async contact(main, site) {
    const sem = await load("seminars");
    main.innerHTML = `
      <section class="page-head"><div class="wrap"><h1>Contact</h1><p>Interested in our research, in a PhD position or in visiting us? Get in touch with any member of the group.</p></div></section>
      <section class="block"><div class="wrap two-col">
        <div class="card"><h3>Address</h3><p>${site.address.map(esc).join("<br>")}</p><p style="margin-top:12px">${link(site.map_url, "Open map →")}</p></div>
        <div class="card"><h3>Seminars</h3><p>${esc(sem.title)}<br>${esc(sem.schedule)}, ${esc(sem.room)}</p>
          ${site.email ? `<h3 style="margin-top:18px">Email</h3><p><a href="mailto:${esc(site.email)}">${esc(site.email)}</a></p>` : ""}</div>
      </div></section>`;
  },
};

/* ---------- Helicoid ↔ catenoid animation ---------- */
function drawSurface(canvas) {
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const NU = 40, NV = 16, VMAX = 1.25, TILT = 0.38;
  const t0 = performance.now();

  function frame(now) {
    const dpr = devicePixelRatio || 1, w = canvas.clientWidth, h = canvas.clientHeight;
    if (canvas.width !== Math.round(w * dpr)) { canvas.width = Math.round(w * dpr); canvas.height = Math.round(h * dpr); }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const s = reduce ? 4 : (now - t0) / 1000;
    const a = ((1 - Math.cos(s * 0.4)) / 2) * (Math.PI / 2); // 0 = helicoid, π/2 = catenoid
    const rot = s * 0.25;
    const ca = Math.cos(a), sa = Math.sin(a), cr = Math.cos(rot), sr = Math.sin(rot);
    const S = Math.min(w, h) / 6.2, cx = w / 2, cy = h / 2 - 8;
    const col = getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();

    const P = (u, v) => {
      const x = ca * Math.sinh(v) * Math.sin(u) + sa * Math.cosh(v) * Math.cos(u);
      const y = -ca * Math.sinh(v) * Math.cos(u) + sa * Math.cosh(v) * Math.sin(u);
      const z = u * ca + v * sa;
      const x1 = x * cr - y * sr, y1 = x * sr + y * cr;
      const Y = z * Math.cos(TILT) - y1 * Math.sin(TILT);
      const depth = y1 * Math.cos(TILT) + z * Math.sin(TILT);
      return [cx + x1 * S, cy - Y * S * 0.9, depth];
    };
    const line = (pts) => {
      for (let k = 1; k < pts.length; k++) {
        const [x0, y0, d0] = pts[k - 1], [x1, y1, d1] = pts[k];
        ctx.globalAlpha = Math.max(0.12, Math.min(0.9, 0.5 - (d0 + d1) / 8));
        ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
      }
    };
    ctx.strokeStyle = col; ctx.lineWidth = 1;
    for (let i = 0; i <= NU; i++) {
      const u = -Math.PI + (2 * Math.PI * i) / NU, pts = [];
      for (let j = 0; j <= 24; j++) pts.push(P(u, -VMAX + (2 * VMAX * j) / 24));
      line(pts);
    }
    for (let j = 0; j <= NV; j++) {
      const v = -VMAX + (2 * VMAX * j) / NV, pts = [];
      for (let i = 0; i <= 60; i++) pts.push(P(-Math.PI + (2 * Math.PI * i) / 60, v));
      line(pts);
    }
    ctx.globalAlpha = 1;
    if (!reduce) requestAnimationFrame(frame);
  }
  requestAnimationFrame(frame);
}

/* ---------- Boot ---------- */
(async function () {
  const main = document.getElementById("content");
  try {
    const site = await load("site");
    buildChrome(site);
    await pages[document.body.dataset.page](main, site);
    if (window.renderMathInElement) renderMathInElement(main, { delimiters: [{ left: "$$", right: "$$", display: true }, { left: "$", right: "$", display: false }], throwOnError: false });
  } catch (err) {
    main.innerHTML = `<div class="wrap" style="padding:40px 20px"><p>Could not load the page data (${esc(err.message)}). If you opened the file directly, start a local server: <code>python3 -m http.server</code>.</p></div>`;
    console.error(err);
  }
})();
