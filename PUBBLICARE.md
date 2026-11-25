# Come pubblicare il sito su GitHub Pages

La cartella `sito-web-dg` è pronta: contiene solo i file del sito (55 file, circa 1 MB).

## 1. Crea l'organizzazione del gruppo (una volta sola)
1. Su github.com, in alto a destra: **+ → New organization → Free**.
2. Nome: `dg-unica` (se è libero). Email: la tua.
3. Puoi saltare l'invito ai colleghi: lo fai dopo da **People**.

## 2. Crea il repository del sito
1. Dalla pagina dell'organizzazione: **Repositories → New repository**.
2. Nome del repository: **`dg-unica.github.io`** (esattamente così: nome dell'organizzazione + `.github.io`).
   Il sito sarà allora all'indirizzo **https://dg-unica.github.io**.
3. Visibilità: **Public** (GitHub Pages gratuito richiede un repository pubblico).
4. Non spuntare "Add a README", poi **Create repository**.

## 3. Carica i file
1. Nella pagina del repository vuoto, clicca il link **"uploading an existing file"**.
2. Apri la cartella `sito-web-dg` nel Finder, seleziona **tutto il contenuto** (⌘A: i file `.html`,
   le cartelle `assets`, `data`, `tools`, i file `README.md` e `PUBBLICARE.md`) e trascinalo nella pagina.
   Trascina il contenuto, non la cartella `sito-web-dg` stessa.
3. Aspetta che finisca il caricamento, poi in basso **Commit changes**.

## 4. Attiva GitHub Pages
1. Nel repository: **Settings → Pages**.
2. In **Build and deployment**: Source **Deploy from a branch**, Branch **main**, cartella **/ (root)**, poi **Save**.
3. Dopo uno o due minuti il sito è online su https://dg-unica.github.io
   (in **Settings → Pages** compare il link quando è pronto).

## Aggiornare il sito
- **Piccole modifiche** (un seminario, un visitatore, un abstract): apri il file su GitHub
  (es. `data/seminars.yml`), clicca la matita ✏️, modifica, poi **Commit changes**.
  Il sito si aggiorna da solo in un minuto.
- **Molti file** (es. dopo aver lanciato gli script per pubblicazioni e preprint):
  **Add file → Upload files** e trascina i file modificati; quelli con lo stesso nome vengono sostituiti.
- Più comodo a lungo termine: l'app gratuita **GitHub Desktop** (desktop.github.com) tiene
  sincronizzata la cartella del computer con GitHub: modifichi in locale, poi "Commit" e "Push".
- Se modifichi `assets/site.js` o `assets/style.css`, cambia il numero `?v=...` nei file `.html`
  (vedi README.md).

## Un indirizzo unica.it (facoltativo)
Si può chiedere ai servizi informatici dell'Ateneo un sottodominio (es. `dgunica.unica.it`)
che punti a GitHub Pages: serve un record DNS di tipo CNAME verso `dg-unica.github.io`.
Poi in **Settings → Pages → Custom domain** si scrive il sottodominio.
