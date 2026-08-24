#!/usr/bin/env python3
"""Build the Plaud capture desk from recordings.json + verticals.json."""
from __future__ import annotations

import html
import json
import re
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
NOTES = ROOT / "notes"
REV = "PLAUD-NOTES-2026-08-24-B"

CSS = """
:root {
  --bg: #090908;
  --bg-2: #11110f;
  --bg-3: #181714;
  --ink: #f0eadc;
  --muted: #8d8778;
  --faint: #5c574c;
  --line: #26241e;
  --accent: #c4452d;
  --mustard: #c4a35a;
  --blue: #6f8fbf;
  --ok: #7d9a6d;
  --serif: "Fraunces", "Iowan Old Style", Georgia, serif;
  --sans: "Source Sans 3", "Source Sans Pro", -apple-system, sans-serif;
  --mono: "IBM Plex Mono", ui-monospace, monospace;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: var(--bg); color: var(--ink); }
body {
  font-family: var(--sans);
  min-height: 100vh;
  text-wrap: pretty;
}
a { color: inherit; }
.shell { display: grid; grid-template-columns: 260px 1fr; min-height: 100vh; }
.rail {
  border-right: 1px solid var(--line);
  padding: 28px 18px 40px;
  background: var(--bg-2);
  position: sticky; top: 0; height: 100vh; overflow: auto;
}
.mark {
  font-family: var(--serif);
  font-weight: 500;
  font-size: 13px;
  letter-spacing: .18em;
  text-transform: uppercase;
  color: var(--accent);
}
.rail h1 {
  font-family: var(--serif);
  font-size: 28px;
  font-weight: 460;
  letter-spacing: -.03em;
  margin: 10px 0 6px;
}
.rail .lede { color: var(--muted); font-size: 13.5px; line-height: 1.45; margin-bottom: 28px; }
.vnav { display: flex; flex-direction: column; gap: 4px; }
.vnav a {
  display: flex; justify-content: space-between; align-items: baseline;
  text-decoration: none; padding: 9px 10px; border-radius: 8px;
  color: var(--ink); font-size: 14px;
}
.vnav a:hover, .vnav a.is-on { background: var(--bg-3); }
.vnav a.is-on { box-shadow: inset 2px 0 0 var(--accent); }
.vnav .count { color: var(--faint); font-family: var(--mono); font-size: 11px; }
.stage { padding: 36px 40px 80px; max-width: 980px; }
.kicker {
  font-size: 11px; letter-spacing: .16em; text-transform: uppercase;
  color: var(--accent); font-weight: 700; margin-bottom: 8px;
}
.stage > h2 {
  font-family: var(--serif); font-weight: 460; font-size: 34px;
  letter-spacing: -.03em; margin-bottom: 8px;
}
.blurb { color: var(--muted); margin-bottom: 28px; max-width: 46rem; }
.empty {
  border: 1px dashed var(--line); border-radius: 14px;
  padding: 36px 28px; color: var(--muted); background: var(--bg-2);
}
.empty strong { color: var(--ink); font-weight: 600; }
.cards { display: flex; flex-direction: column; gap: 10px; }
.card {
  display: grid; grid-template-columns: 1fr auto; gap: 12px;
  text-decoration: none; padding: 16px 18px; border-radius: 12px;
  background: var(--bg-2); border: 1px solid var(--line);
}
.card:hover { border-color: #3a372e; background: var(--bg-3); }
.card h3 { font-size: 16px; font-weight: 600; margin-bottom: 4px; }
.meta { color: var(--muted); font-size: 13px; display: flex; gap: 10px; flex-wrap: wrap; }
.chip {
  font-family: var(--mono); font-size: 10px; letter-spacing: .06em;
  text-transform: uppercase; padding: 3px 7px; border-radius: 999px;
  border: 1px solid var(--line); color: var(--muted); height: fit-content;
}
.chip.dealers { color: var(--blue); border-color: #2a3344; }
.chip.avec-tous { color: var(--mustard); border-color: #3a3320; }
.chip.personal { color: #c9a7a0; }
.chip.ideas { color: var(--ok); }
.note-top { margin-bottom: 22px; }
.note-top h2 { font-family: var(--serif); font-size: 36px; font-weight: 460; letter-spacing: -.03em; }
.tabs { display: flex; gap: 6px; margin: 22px 0 18px; border-bottom: 1px solid var(--line); }
.tabs button {
  appearance: none; background: none; border: 0; color: var(--muted);
  font: 600 13px var(--sans); padding: 10px 12px; cursor: pointer;
  border-bottom: 2px solid transparent; margin-bottom: -1px;
}
.tabs button[aria-selected="true"] { color: var(--ink); border-bottom-color: var(--accent); }
.panel { display: none; }
.panel.is-on { display: block; }
.prose { font-size: 16.5px; line-height: 1.6; max-width: 42rem; }
.prose h2, .prose h3 { font-family: var(--serif); font-weight: 500; margin: 1.3em 0 .4em; }
.prose p { margin: 0 0 .8em; }
.prose ul, .prose ol { margin: 0 0 1em 1.2em; }
.prose li { margin: .25em 0; }
.hl { border-left: 2px solid var(--accent); padding: 10px 0 10px 14px; margin: 0 0 14px; }
.hl .t { font-family: var(--mono); font-size: 11px; color: var(--faint); }
.hl h4 { font-size: 15px; margin: 4px 0; }
.hl p { color: var(--muted); font-size: 14.5px; }
.seg { display: grid; grid-template-columns: 64px 1fr; gap: 12px; padding: 8px 0; border-bottom: 1px solid var(--line); }
.seg .ts { font-family: var(--mono); font-size: 11px; color: var(--faint); padding-top: 3px; }
.back { color: var(--muted); text-decoration: none; font-size: 13px; display: inline-block; margin-bottom: 18px; }
.back:hover { color: var(--ink); }
footer { margin-top: 48px; color: var(--faint); font-size: 11px; font-family: var(--mono); }
@media (max-width: 820px) {
  .shell { grid-template-columns: 1fr; }
  .rail { position: relative; height: auto; border-right: 0; border-bottom: 1px solid var(--line); }
  .stage { padding: 24px 18px 64px; }
  .note-top h2 { font-size: 28px; }
}
"""


def load() -> tuple[list[dict], list[dict]]:
    verticals = json.loads((ROOT / "verticals.json").read_text())["verticals"]
    rec_path = ROOT / "recordings.json"
    recs = []
    if rec_path.exists():
        data = json.loads(rec_path.read_text())
        recs = data.get("recordings") or []
    return verticals, recs


def esc(s: object) -> str:
    return html.escape("" if s is None else str(s))


def dur(ms: int) -> str:
    s = max(0, int(ms or 0) // 1000)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    if h:
        return f"{h}h{m:02d}m"
    if m:
        return f"{m}m{s:02d}s"
    return f"{s}s"


def day(iso: str) -> str:
    if not iso:
        return ""
    try:
        return datetime.fromisoformat(iso.replace("Z", "")).strftime("%Y-%m-%d")
    except Exception:
        return iso[:10]


def ts(ms: int) -> str:
    s = max(0, int(ms or 0) // 1000)
    m, s = divmod(s, 60)
    return f"{m}:{s:02d}"


def md(text: str) -> str:
    if not text:
        return "<p class='empty'>No summary yet.</p>"
    lines = text.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    buf: list[str] = []
    in_list = False

    def flush_p() -> None:
        nonlocal buf
        if buf:
            out.append("<p>" + " ".join(buf) + "</p>")
            buf = []

    def inline(s: str) -> str:
        s = esc(s)
        s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
        s = re.sub(r"`(.+?)`", r"<code>\1</code>", s)
        return s

    for raw in lines:
        line = raw.rstrip()
        if not line.strip():
            flush_p()
            if in_list:
                out.append("</ul>")
                in_list = False
            continue
        if line.startswith("## "):
            flush_p()
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h2>{inline(line[3:])}</h2>")
            continue
        if line.startswith("### "):
            flush_p()
            if in_list:
                out.append("</ul>")
                in_list = False
            out.append(f"<h3>{inline(line[4:])}</h3>")
            continue
        if line.startswith("- ") or line.startswith("* "):
            flush_p()
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline(line[2:])}</li>")
            continue
        buf.append(inline(line))
    flush_p()
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def page(title: str, body: str, extra_js: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="robots" content="noindex, nofollow">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{esc(title)}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,500&family=IBM+Plex+Mono:wght@400;500&family=Source+Sans+3:wght@400;600;700&display=swap">
  <style>{CSS}</style>
</head>
<body>
{body}
<footer>{esc(REV)} · noindex · Plaud sources + notes</footer>
<script>
{extra_js}
</script>
</body>
</html>
"""


def rail(verticals: list[dict], counts: dict[str, int], on: str, prefix: str = "") -> str:
    links = [
        f'<a href="{prefix}index.html" class="{"is-on" if on=="all" else ""}">All <span class="count">{sum(counts.values())}</span></a>'
    ]
    for v in verticals:
        cls = "is-on" if on == v["id"] else ""
        href = f'{prefix}vertical-{v["id"]}.html'
        links.append(
            f'<a class="{cls}" href="{href}">{esc(v["label"])} <span class="count">{counts.get(v["id"], 0)}</span></a>'
        )
    return f"""<aside class="rail">
  <div class="mark">Cooperative</div>
  <h1>Field desk</h1>
  <p class="lede">Plaud landings. Summary, highlights, transcript — filed by life area.</p>
  <nav class="vnav">{"".join(links)}</nav>
</aside>"""


def card(rec: dict, prefix: str = "") -> str:
    href = f'{prefix}notes/{esc(rec["id"])}.html'
    return f"""<a class="card" href="{href}">
  <div>
    <h3>{esc(rec.get("name") or rec["id"])}</h3>
    <div class="meta"><span>{esc(day(rec.get("start_at") or rec.get("created_at") or ""))}</span><span>{esc(dur(rec.get("duration_ms") or 0))}</span></div>
  </div>
  <span class="chip {esc(rec.get("vertical") or "inbox")}">{esc(rec.get("vertical") or "inbox")}</span>
</a>"""


def list_page(verticals: list[dict], recs: list[dict], vid: str | None) -> str:
    counts = {v["id"]: 0 for v in verticals}
    for r in recs:
        counts[r.get("vertical") or "inbox"] = counts.get(r.get("vertical") or "inbox", 0) + 1
    if vid:
        v = next(x for x in verticals if x["id"] == vid)
        title, kicker, blurb = v["label"], "Vertical", v["blurb"]
        shown = [r for r in recs if (r.get("vertical") or "inbox") == vid]
        on = vid
    else:
        title, kicker, blurb = "All landings", "Plaud capture", "Every real note. Tests stay out."
        shown = recs
        on = "all"
    shown = sorted(shown, key=lambda r: r.get("start_at") or "", reverse=True)
    body_list = (
        '<div class="cards">' + "".join(card(r) for r in shown) + "</div>"
        if shown
        else f'<div class="empty"><strong>Nothing filed here yet.</strong><br>Record something over ~30s and name the dest, or Ada will infer it.</div>'
    )
    inner = f"""<div class="shell">
{rail(verticals, counts, on)}
<main class="stage">
  <div class="kicker">{esc(kicker)}</div>
  <h2>{esc(title)}</h2>
  <p class="blurb">{esc(blurb)}</p>
  {body_list}
</main>
</div>"""
    return page(f"{title} — Field desk", inner)


def note_page(verticals: list[dict], rec: dict, recs: list[dict]) -> str:
    counts = {v["id"]: 0 for v in verticals}
    for r in recs:
        counts[r.get("vertical") or "inbox"] = counts.get(r.get("vertical") or "inbox", 0) + 1
    highlights = rec.get("highlights") or []
    segs = rec.get("transcript") or []
    hl_html = "".join(
        f'<div class="hl"><div class="t">{esc(ts(h.get("timestamp") or 0))}</div><h4>{esc(h.get("title") or "Highlight")}</h4><p>{esc(h.get("content") or "")}</p></div>'
        for h in highlights
    ) or "<div class='empty'>No device highlights on this take.</div>"
    tx_html = "".join(
        f'<div class="seg"><div class="ts">{esc(ts(s.get("start_time") or s.get("start") or 0))}</div><div>{esc(s.get("content") or s.get("text") or "")}</div></div>'
        for s in segs
    ) or "<div class='empty'>No transcript yet.</div>"
    js = """
document.querySelectorAll('.tabs button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tabs button').forEach(b => b.setAttribute('aria-selected', b===btn ? 'true':'false'));
    document.querySelectorAll('.panel').forEach(p => p.classList.toggle('is-on', p.id === btn.dataset.panel));
  });
});
"""
    inner = f"""<div class="shell">
{rail(verticals, counts, rec.get("vertical") or "inbox", prefix="../")}
<main class="stage">
  <a class="back" href="../index.html">← Desk</a>
  <div class="note-top">
    <div class="kicker">{esc(rec.get("vertical") or "inbox")} · {esc(day(rec.get("start_at") or ""))} · {esc(dur(rec.get("duration_ms") or 0))}</div>
    <h2>{esc(rec.get("name") or rec["id"])}</h2>
    <div class="meta" style="margin-top:8px"><span>id {esc(rec["id"])}</span><span>{esc(rec.get("routed_by") or "")}</span></div>
  </div>
  <div class="tabs" role="tablist">
    <button type="button" data-panel="sum" aria-selected="true">Summary</button>
    <button type="button" data-panel="hl" aria-selected="false">Highlights</button>
    <button type="button" data-panel="tx" aria-selected="false">Transcript</button>
  </div>
  <section id="sum" class="panel is-on prose">{md(rec.get("summary_md") or "")}</section>
  <section id="hl" class="panel">{hl_html}</section>
  <section id="tx" class="panel">{tx_html}</section>
</main>
</div>"""
    return page(rec.get("name") or rec["id"], inner, js)


def main() -> int:
    NOTES.mkdir(exist_ok=True)
    verticals, recs = load()
    (ROOT / "index.html").write_text(list_page(verticals, recs, None), encoding="utf-8")
    for v in verticals:
        (ROOT / f'vertical-{v["id"]}.html').write_text(list_page(verticals, recs, v["id"]), encoding="utf-8")
    for rec in recs:
        (NOTES / f'{rec["id"]}.html').write_text(note_page(verticals, rec, recs), encoding="utf-8")
    # keep recordings.json as the mutable registry; don't wipe extra keys
    registry = {"revision": REV, "recordings": recs}
    (ROOT / "recordings.json").write_text(json.dumps(registry, indent=2) + "\n", encoding="utf-8")
    print(f"built {1+len(verticals)} indexes, {len(recs)} notes, {REV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
