# DG-UniCa website

Static website of the Differential Geometry group, University of Cagliari.

## How to update the content
Everything is in the `data/` folder. You do not need to touch the HTML or JS files:

| File | Content |
|---|---|
| `data/site.yml` | Name, introduction, address, opportunities for students |
| `data/people.yml` | Faculty, PhD/post-docs, alumni, collaborators |
| `data/research.yml` | Research topics |
| `data/seminars.yml` | Seminars (upcoming/past are computed automatically from the date) |
| `data/events.yml` | Conferences and workshops |
| `data/publications.yml` | Publications since 2000 |
| `data/preprints.yml` | Recent arXiv preprints (Preprints page and home page box) |
| `data/visitors.yml` | Visitors currently in the department (home page); with an `until:` date they disappear by themselves |

Math can be written in LaTeX between `$...$`.

## Preview locally
```bash
cd sito-web-dg
python3 -m http.server 8000
```
then open http://localhost:8000

## After changing the code or the style
If you edit `assets/site.js` or `assets/style.css`, change the `?v=...` number in the
`<script>` and `<link>` tags of the `.html` files, so browsers download the new version
instead of using an old cached copy. Data files in `data/` are always reloaded.

## Updating the publications
```bash
python3 tools/fetch_publications.py
```
downloads all papers of the group since 2000 from zbMATH Open and merges them with
`data/publications.yml`, keeping manual corrections. It also adds the arXiv link
(`arxiv:` field) when zbMATH knows it, or when arXiv has a paper with the same title and a
common author. `arxiv: ""` means the paper was searched and not found; write the link by hand
if you know it. Use `--no-arxiv-search` to skip the (slow) arXiv search.

## Updating the arXiv preprints (home page box)
```bash
python3 tools/fetch_preprints.py
```
looks on arXiv for papers of the faculty and PhD students (last 24 months, mathematics only)
that are not yet published, i.e. without journal reference or DOI on arXiv and not already in
`data/publications.yml`. The home page shows the 5 most recent. To hide a wrong match (e.g. a
homonym), add its arXiv id to `exclude:` in `data/preprints.yml`.

## Regenerating the research figures
```bash
python3 tools/make_figures.py
```
