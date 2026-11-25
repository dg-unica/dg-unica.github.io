"""Rebuild data/publications.yml from zbMATH Open (all papers of the group since 2000).

Usage:  python3 tools/fetch_publications.py
Needs:  internet access, and Ruby (preinstalled on macOS) to read the existing YAML file.

How it works
- Downloads from the zbMATH Open API every document (journal article, article in a
  collection, book) published since START_YEAR by the authors listed in AUTHORS.
- Merges it with the current data/publications.yml: entries already there (matched by DOI
  or by title) are kept as they are, so manual corrections and "topics" survive; entries that
  zbMATH does not know (e.g. very recent papers) are kept too.
- New entries get research topics guessed from title, keywords and MSC codes (see guess_topics).
  The guess can be corrected by editing the "topics" line in the YAML file.
"""
import difflib
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data", "publications.yml")
START_YEAR = 2000
END_YEAR = 2026

# zbMATH author codes of current and former members of the group
AUTHORS = [
    "bande.gianluca", "cappelletti-montano.beniamino", "loi.andrea", "montaldo.stefano",
    "mossa.roberto", "onnis.irene-ignazia", "piu.paola", "piu.m-paola", "placini.giovanni",
    "provenzano.luigi", "ratto.andrea", "zuddas.fabio", "damele.marco", "sanna.antonio",
    "caddeo.renzo",
]
KEEP_TYPES = {"j", "a", "b"}  # journal article, article in a collection, book

# Only mathematics: leave out economics, bibliometrics and history/music books.
EXCLUDE_JOURNALS = re.compile(r"Econ|J\. Classif", re.I)
EXCLUDE_TEXT = re.compile(r"GREAM|eighteenth century", re.I)


def excluded(e):
    return bool(EXCLUDE_JOURNALS.search(e.get("journal") or "")
                or EXCLUDE_TEXT.search(f'{e.get("title", "")} {e.get("details", "")}'))


def api(params):
    url = "https://api.zbmath.org/v1/document/_search?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 404:  # zbMATH answers 404 when a search has no results
                return {"result": []}
            print("  retry", attempt + 1, e, file=sys.stderr)
            time.sleep(3 * (attempt + 1))
        except Exception as e:  # retry on transient errors / rate limits
            print("  retry", attempt + 1, e, file=sys.stderr)
            time.sleep(3 * (attempt + 1))
    raise RuntimeError("zbMATH API not reachable")


def fetch(code):
    docs, page = [], 0
    while True:
        d = api({"search_string": f"ai:{code} py:{START_YEAR}-{END_YEAR}", "page": page, "results_per_page": 100})
        res = d.get("result") or []
        docs += res
        if len(res) < 100:
            return docs
        page += 1
        time.sleep(0.5)


def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


def short_name(name):
    """'Montaldo, Stefano' / 'Montaldo, S.' -> 'S. Montaldo'."""
    if "," not in name:
        return name
    last, first = [x.strip() for x in name.split(",", 1)]
    parts = re.split(r"([\s-]+)", first)
    out = ""
    for p in parts:
        if not p.strip() or p.strip() == "-":
            out += "-" if "-" in p else " "
        else:
            out += p[0] + "."
    return f"{re.sub(r'  +', ' ', out).strip()} {last}"


def tex(s):
    s = (s or "").strip()
    s = s.replace("\\(", "$").replace("\\)", "$")
    return s[:-1] if s.endswith(".") and not s.endswith("..") else s


def guess_topics(text, msc):
    t = text.lower()
    has = lambda *ws: any(w in t for w in ws)
    m = lambda *ps: any(c.startswith(p) for c in msc for p in ps)
    topics = []
    if (has("harmonic map", "biharmonic", "polyharmonic", "triharmonic", "biconservative", "bienergy",
            "harmonic morphism", "r-harmonic", "energy functional", "tension field", "biharmonic function")
            or m("58E20", "53C43")) and not has("harmonic form"):
        topics.append("harmonic-maps")
    if has("contact", "symplectic pair", "foliation", "reeb", "recursion operator", "harmonic form",
           "symplectic") and not has("sasak"):
        topics.append("contact-geometry")
    if has("kähler", "kaehler", "kahler", "fubini", "bergman", "hartogs", "quantiz", "berezin", "szeg",
           "hermitian symmetric", "projective space", "flag manifold", "symmetric domain", "balanced metric"):
        topics.append("kahler-geometry")
    if has("cohomolog", "formal", "massey", "lefschetz", "dolbeault", "almost complex", "bott-chern",
           "aeppli", "hodge", "betti"):
        topics.append("complex-cohomology")
    if has("holomorphic isometr", "kähler immersion", "kaehler immersion", "diastasis", "projectively induced",
           "relatives", "complex space form", "isometric immersion", "holomorphic immersion", "induced by"):
        topics.append("holomorphic-isometries")
    if has("surface", "helix", "loxodrom", "constant mean curvature", "björling", "bjorling", "bour",
           "helicoid", "constant angle", "catenoid", "minimal immersion") or m("53A10", "53A05"):
        topics.append("special-surfaces")
    if has("sasak", "vaisman", "locally conformally k", "k-contact"):
        topics.append("sasakian-vaisman")
    if has("eigenvalue", "eigenfunction", "steklov", "spectral", "spectrum", "laplacian", "nodal",
           "faber", "magnetic") or m("35P", "58J50"):
        topics.append("spectral-geometry")
    return topics


def entry_from_zb(doc):
    authors = ", ".join(short_name(a["name"]) for a in doc["contributors"]["authors"])
    title = tex(doc["title"]["title"])
    if doc["title"].get("subtitle"):
        title += ": " + tex(doc["title"]["subtitle"])
    year = int(doc["year"]) if str(doc.get("year", "")).isdigit() else None
    src = doc["source"]
    series = (src.get("series") or [{}])[0]
    if doc["document_type"]["code"] == "j" and series.get("short_title"):
        journal = series["short_title"]
        details = f'{series.get("volume") or ""} ({year})'.strip()
        if series.get("issue"):
            details += f', no. {series["issue"]}'
        if src.get("pages"):
            details += f', {src["pages"].replace("-", "–")}'
    else:
        journal = ""
        details = re.sub(r"\s+", " ", (src.get("source") or "")).strip().rstrip(".")
    doi = next((l["identifier"] for l in doc.get("links", []) if l.get("type") == "doi"), None)
    arxiv = next((l["identifier"] for l in doc.get("links", []) if l.get("type") == "arxiv"), None)
    url = f"https://doi.org/{doi}" if doi else f'https://zbmath.org/?q=an:{doc["identifier"]}'
    msc = [c["code"] for c in doc.get("msc", [])]
    kw = " ".join(doc.get("keywords") or [])
    return {
        "authors": authors, "title": title, "journal": journal, "details": details, "year": year,
        "url": url, "arxiv": f"https://arxiv.org/abs/{arxiv}" if arxiv else "",
        "topics": guess_topics(f"{title} {kw}", msc), "_doi": (doi or "").lower(),
    }


def arxiv_search(e):
    """Look for the paper on arXiv by title; accept only a near-identical title with a shared author."""
    words = re.findall(r"[A-Za-z]{3,}", re.sub(r"\$[^$]*\$", " ", e["title"]))[:12]
    if len(words) < 2:
        return None
    q = " AND ".join(f"ti:{w}" for w in words)
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": q, "max_results": 10})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                xml = r.read().decode()
            break
        except Exception as ex:
            print("  arXiv retry", attempt + 1, ex, file=sys.stderr)
            time.sleep(10)
    else:
        return None
    surnames = {norm(a.split()[-1]) for a in e["authors"].split(",") if a.strip()}
    for entry in re.findall(r"<entry>(.*?)</entry>", xml, re.S):
        t = re.search(r"<title>(.*?)</title>", entry, re.S).group(1)
        names = {norm(n.split()[-1]) for n in re.findall(r"<name>(.*?)</name>", entry)}
        same = difflib.SequenceMatcher(None, norm(t), norm(e["title"])).ratio() > 0.9
        if same and surnames & names:
            aid = re.search(r"<id>https?://arxiv.org/abs/(.*?)</id>", entry).group(1)
            return "https://arxiv.org/abs/" + re.sub(r"v\d+$", "", aid)
    return None


def search_arxiv(entries):
    """Fill missing arXiv links (papers from 1992 on). Entries with arxiv: "" are left alone."""
    todo = [e for e in entries if "arxiv" not in e and e.get("year", 0) >= 1992]
    print(f"searching arXiv for {len(todo)} papers (about {len(todo) * 3 // 60 + 1} min)", file=sys.stderr)
    for e in todo:
        e["arxiv"] = arxiv_search(e) or ""
        time.sleep(3)  # arXiv asks for at most one request every 3 seconds


def load_existing():
    rb = 'require "yaml"; require "json"; puts JSON.generate(YAML.load_file(ARGV[0]))'
    return json.loads(subprocess.check_output(["ruby", "-e", rb, DATA]))


def dump(entries):
    q = lambda s: json.dumps(s, ensure_ascii=False)
    lines = ["# Publications of the group (newest first). Generated by tools/fetch_publications.py",
             "# from zbMATH Open and then edited by hand: manual changes are kept when the script runs again.",
             "# topics: research slugs (see research.yml); the paper then appears on those topic pages.",
             "# LaTeX between $...$ is allowed in titles.", ""]
    year = None
    for e in entries:
        if e.get("year") != year:
            year = e.get("year")
            lines.append(f"# ---------------- {year} ----------------")
        lines.append(f'- authors: {q(e["authors"])}')
        lines.append(f'  title: {q(e["title"])}')
        lines.append(f'  journal: {q(e.get("journal") or "")}')
        lines.append(f'  details: {q(e.get("details") or "")}')
        lines.append(f'  year: {e["year"]}')
        lines.append(f'  url: {q(e["url"])}')
        if "arxiv" in e:  # "" means: searched, not on arXiv
            lines.append(f'  arxiv: {q(e["arxiv"])}')
        if e.get("topics"):
            lines.append(f'  topics: [{", ".join(e["topics"])}]')
    with open(DATA, "w") as f:
        f.write("\n".join(lines) + "\n")


def main():
    found = {}
    for code in AUTHORS:
        docs = fetch(code)
        kept = 0
        for d in docs:
            if d["document_type"]["code"] in KEEP_TYPES and d["id"] not in found:
                found[d["id"]] = entry_from_zb(d)
                kept += 1
        print(f"{code}: {len(docs)} documents, {kept} new", file=sys.stderr)
        time.sleep(0.5)

    existing = load_existing()
    by_doi = {e["url"].lower().split("doi.org/")[-1]: e for e in existing if "doi.org/" in e.get("url", "")}
    by_title = {norm(e["title"]): e for e in existing}
    merged, used = [], set()
    for z in found.values():
        old = by_doi.get(z["_doi"]) if z["_doi"] else None
        old = old or by_title.get(norm(z["title"]))
        if old is not None:
            used.add(id(old))
            if z["arxiv"] and not old.get("arxiv"):
                old["arxiv"] = z["arxiv"]  # add the arXiv link zbMATH knows about
            continue
        if not z["arxiv"]:
            del z["arxiv"]  # not known to zbMATH: search_arxiv will look for it
        merged.append(z)
    merged += existing  # keep every existing entry as it is
    # drop exact duplicates that may come from zbMATH itself (same title and year)
    seen, final = set(), []
    for e in merged:
        k = (norm(e["title"]), e.get("year"))
        if k not in seen:
            seen.add(k)
            final.append(e)
    final = [e for e in final if e.get("year") and e["year"] >= START_YEAR and not excluded(e)]
    final.sort(key=lambda e: -e["year"])
    if "--no-arxiv-search" not in sys.argv:
        search_arxiv(final)
    dump(final)
    print(f"{len(final)} publications written ({len(final) - len(existing)} added)", file=sys.stderr)


if __name__ == "__main__":
    main()
