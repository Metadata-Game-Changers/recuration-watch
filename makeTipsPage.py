#!/usr/bin/env python3
"""Regenerate tips.html (English) and tips.es.html (Spanish) from the tips arrays
embedded in the tool pages.

The while-you-wait tips live in each tool (the source of truth):
    recurationWatch.html          RCW_TIPS
    completeness.html             COMPLETENESS_TIPS
    metadataConnectivity.html     CONNECTIVITY_TIPS
    rorRetriever.html             TIPS
    orcidRetriever.html           TIPS
    repositoryHistory.html        HISTORY_TIPS
    organizationCompleteness.html ORG_TIPS

Spanish translations live in tipsTranslations.es.json, keyed by tool file and the
ENGLISH tip label. A tip without a translation falls back to English with a
warning (and fails --check), so add the translation when you add the tip.

After adding or editing a tip in a tool (or a translation), re-run:

    python3 makeTipsPage.py            # rewrite tips.html + tips.es.html
    python3 makeTipsPage.py --check    # exit 1 if either page is stale or a
                                       # translation is missing (no write)

Stdlib only; expects the tip objects on one line each in the form
    { label:'…', text:'…', link:'…' },
which is the convention in every tool page.
"""
import html
import json
import re
import sys

TOOLS = [
    ("recurationWatch.html", "RCW_TIPS", "Re-Curation Watch"),
    ("completeness.html", "COMPLETENESS_TIPS", "Metadata Completeness"),
    ("metadataConnectivity.html", "CONNECTIVITY_TIPS", "Metadata Connectivity"),
    ("rorRetriever.html", "TIPS", "ROR Retriever"),
    ("orcidRetriever.html", "TIPS", "ORCID Retriever"),
    ("repositoryHistory.html", "HISTORY_TIPS", "Repository History"),
    ("organizationCompleteness.html", "ORG_TIPS", "Organization Completeness"),
]

TRANSLATIONS_FILE = "tipsTranslations.es.json"

TIP_RE = re.compile(
    r"\{\s*label:\s*'((?:[^'\\]|\\.)*)',\s*text:\s*'((?:[^'\\]|\\.)*)',\s*link:\s*'((?:[^'\\]|\\.)*)'\s*\}"
)


def js_str(s):
    """Decode the JS single-quoted string escapes used in the tips arrays."""
    s = re.sub(r"\\u([0-9a-fA-F]{4})", lambda m: chr(int(m.group(1), 16)), s)
    return s.replace("\\'", "'").replace("\\\\", "\\")


def collect():
    collected = []
    for fname, var, name in TOOLS:
        src = open(fname, encoding="utf-8").read()
        m = re.search(re.escape("const " + var + " = [") + r"(.*?)\n\];", src, re.S)
        if not m:
            sys.exit(f"ERROR: no `const {var} = [` array found in {fname}")
        tips = [tuple(js_str(g) for g in t) for t in TIP_RE.findall(m.group(1))]
        if not tips:
            sys.exit(f"ERROR: {var} in {fname} matched no tips — format drift?")
        collected.append((fname, name, tips))
    return collected


def translate(collected, translations):
    """(collected in Spanish, [missing '<file>: <label>' strings]).

    Keys into translations by tool file + English label; a tip without an entry
    keeps its English label/text. An entry may carry an optional 'link' override.
    """
    out, missing = [], []
    for fname, name, tips in collected:
        table = translations.get(fname, {})
        es_tips = []
        for label, text, link in tips:
            t = table.get(label)
            if t:
                es_tips.append((t["label"], t["text"], t.get("link", link)))
            else:
                missing.append(f"{fname}: {label}")
                es_tips.append((label, text, link))
        out.append((fname, name, es_tips))
    return out, missing


# Page chrome per language. The [[TOKENS]] in PAGE_HEAD / PAGE_FOOT are filled
# from these dicts; render() asserts none survive substitution.
LANGS = {
    "en": {
        "out": "tips.html",
        "lang": "en",
        "title": "Metadata Tips — Metadata Game Changers",
        "desc": "All the while-you-wait tips from the Metadata Game Changers tools in one place — completeness, connectivity, re-curation, and ROR / ORCID identifier matching.",
        "brand": "Metadata Tips",
        "topbar": """<a href="tips.es.html">Español ↗</a>
      <a href="index.html">All Tools ↗</a>
      <a href="guide.html">Repository Guide ↗</a>
      <a href="consortiumGuide.html">Consortium Guide ↗</a>
      <a href="reading.html">Related Reading ↗</a>
      <a href="https://github.com/Metadata-Game-Changers/recuration-watch/issues/new/choose" target="_blank" rel="noopener">Feedback ↗</a>""",
        "intro": 'Every <a href="index.html">MGC metadata tool</a> shows rotating tips while it works — small pieces of\n  metadata wisdom about completeness, connectivity, identifiers, and re-curation. This page collects all of them in one\n  place, grouped by the tool they appear in.',
        "jump": "Jump to:",
        "open_tool": "Open the tool →",
        "tips_word": "tips",
        "learn_more": "Learn more ↗",
        "foot_lede": "These tips rotate inside the tools while data loads; here they are all at once. Collected from",
        "foot_and": "and",
        "foot_tail": 'A <a href="https://metadatagamechangers.com" target="_blank" rel="noopener">Metadata Game Changers</a> prototype\n    &copy; Metadata Game Changers, licensed under <a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank" rel="noopener">CC BY-NC 4.0</a> · DOI: pending.',
        "banner": 'This site uses Google Analytics for anonymous usage statistics. <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">Google Privacy Policy ↗</a>',
        "banner_ok": "OK",
        "banner_no": "Decline",
    },
    "es": {
        "out": "tips.es.html",
        "lang": "es",
        "title": "Consejos de Metadatos — Metadata Game Changers",
        "desc": "Todos los consejos de las herramientas de Metadata Game Changers en un solo lugar — completitud, conectividad, re-curación y emparejamiento de identificadores ROR / ORCID.",
        "brand": "Consejos de Metadatos",
        "topbar": """<a href="tips.html">English ↗</a>
      <a href="index.es.html">Todas las Herramientas ↗</a>
      <a href="guide.es.html">Guía para Repositorios ↗</a>
      <a href="consortiumGuide.es.html">Guía para Consorcios ↗</a>
      <a href="reading.html">Lecturas Relacionadas ↗ (EN)</a>
      <a href="https://github.com/Metadata-Game-Changers/recuration-watch/issues/new/choose" target="_blank" rel="noopener">Comentarios ↗</a>""",
        "intro": 'Cada <a href="index.es.html">herramienta de metadatos de MGC</a> muestra consejos rotativos mientras trabaja —\n  pequeñas dosis de sabiduría sobre completitud, conectividad, identificadores y re-curación. Esta página los reúne\n  todos en un solo lugar, agrupados por la herramienta en la que aparecen. La interfaz de las herramientas está en inglés.',
        "jump": "Ir a:",
        "open_tool": "Abrir la herramienta →",
        "tips_word": "consejos",
        "learn_more": "Más información ↗",
        "foot_lede": "Estos consejos rotan dentro de las herramientas mientras se cargan los datos; aquí están todos a la vez. Recopilados de",
        "foot_and": "y",
        "foot_tail": 'Un prototipo de <a href="https://metadatagamechangers.com" target="_blank" rel="noopener">Metadata Game Changers</a>\n    &copy; Metadata Game Changers, con licencia <a href="https://creativecommons.org/licenses/by-nc/4.0/" target="_blank" rel="noopener">CC BY-NC 4.0</a> · DOI: pendiente.',
        "banner": 'Este sitio usa Google Analytics para obtener estadísticas de uso anónimas. <a href="https://policies.google.com/privacy" target="_blank" rel="noopener">Política de Privacidad de Google ↗</a>',
        "banner_ok": "Aceptar",
        "banner_no": "Rechazar",
    },
}

PAGE_HEAD = '''<!DOCTYPE html>
<html lang="[[LANG]]">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>[[TITLE]]</title>
<meta name="description" content="[[DESC]]" />
<link rel="icon" type="image/png" href="favicon_MGC.png" />
<link rel="alternate" hreflang="en" href="tips.html" />
<link rel="alternate" hreflang="es" href="tips.es.html" />
<link rel="alternate" hreflang="x-default" href="tips.html" />
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&family=Montserrat:wght@400;500&display=swap" rel="stylesheet" />
<style>
  :root{ --accent:#9167b0; --accent-dk:#673289; --tint:#f0eaf5; --ink:#1f2330; --muted:#6b7280; --line:#e6e3ec; --bg:#fbfafe; --green:#3a9d6e; --amber:#d4910b; --red:#c0392b; }
  *{box-sizing:border-box}
  body{font-family:Inter,system-ui,-apple-system,Segoe UI,Roboto,sans-serif;color:var(--ink);background:var(--bg);margin:0;padding:0}
  .topbar{border-bottom:2px solid var(--ink);padding:0 2rem}
  .topbar-inner{max-width:1040px;margin:0 auto;display:flex;align-items:stretch;gap:0}
  .topbar-brand{padding:.5rem 2rem .3rem 0;display:flex;flex-direction:row;align-items:flex-end;gap:1rem}
  .brand-logo{height:64px;width:auto;display:block;flex-shrink:0}
  .brand-title-wrap{display:flex;flex-direction:column;justify-content:flex-end;padding-bottom:.15rem}
  .brand-tool-name{font-family:'Montserrat',sans-serif;font-size:2rem;font-weight:400;letter-spacing:.02em;color:#673289;line-height:1;white-space:nowrap;text-transform:uppercase}
  .topbar-links{padding:0 0 0 1.5rem;display:flex;flex-direction:column;justify-content:center;gap:.25rem;margin-left:auto}
  .topbar-links a{font-size:.72rem;color:var(--muted);text-decoration:none;white-space:nowrap;line-height:1.4}
  .topbar-links a:hover{color:var(--accent-dk)}
  @media(max-width:820px){.topbar{padding:0 1rem}.topbar-inner{flex-direction:column}.topbar-brand{padding-right:0}.brand-tool-name{font-size:1.5rem}.topbar-links{flex-direction:row;flex-wrap:wrap;gap:.75rem;padding:.25rem 0 .5rem}}
  .wrap{max-width:1080px;margin:0 auto;padding:1.5rem 1.25rem 3rem}
  .intro{font-size:.85rem;color:var(--ink);line-height:1.6;max-width:760px;margin:.4rem 0 1.2rem}
  .intro a{color:var(--accent);text-decoration:none}
  .intro a:hover{text-decoration:underline}
  .jump{font-size:.78rem;line-height:1.9;margin:.2rem 0 1rem;padding:.6rem .9rem;border:1px solid var(--line);border-radius:10px;background:#fff;max-width:760px}
  .jump a{color:var(--accent-dk);text-decoration:none;white-space:nowrap}
  .jump a:hover{text-decoration:underline}
  .tool-group{font-size:.95rem;font-weight:600;color:var(--accent-dk);margin:1.6rem 0 .6rem;border-bottom:1px solid var(--line);padding-bottom:.35rem;display:flex;align-items:baseline;gap:.8rem;flex-wrap:wrap;scroll-margin-top:1rem}
  .tool-group a.open-tool{font-size:.7rem;font-weight:600;color:var(--accent);text-decoration:none}
  .tool-group a.open-tool:hover{color:var(--accent-dk)}
  .tool-group .count{margin-left:auto;font-size:.68rem;color:var(--muted);font-weight:400}
  .tips-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:.7rem}
  .tip{border:1px solid var(--line);border-left:3px solid var(--accent);border-radius:8px;background:#fff;padding:.7rem .9rem}
  .tip .tips-label{font-size:.62rem;text-transform:uppercase;letter-spacing:.05em;color:var(--accent-dk);font-weight:600;margin-bottom:.2rem}
  .tip .tips-text{font-size:.82rem;color:var(--ink);line-height:1.5}
  .tip .tips-text strong{color:var(--accent-dk)}
  .tip .tips-link{display:inline-block;margin-top:.4rem;font-size:.68rem;color:var(--accent);text-decoration:none}
  .tip .tips-link:hover{text-decoration:underline}
  footer{margin-top:2.5rem;font-size:.72rem;color:var(--muted);border-top:1px solid var(--line);padding-top:.9rem;line-height:1.5}
  footer a{color:var(--accent);text-decoration:none}
  @media print{.topbar-links,#analytics-banner{display:none !important} .tip{break-inside:avoid}}
  /* analytics consent banner */
  #analytics-banner{position:fixed;bottom:0;left:0;right:0;background:var(--ink);color:#fff;padding:.75rem 2rem;display:flex;align-items:center;justify-content:space-between;gap:1rem;flex-wrap:wrap;z-index:500;font-size:.75rem;border-top:2px solid #444}
  #analytics-banner a{color:#93c5fd}
  #analytics-banner-btns{display:flex;gap:.5rem}
  .ab-btn{padding:.35rem .85rem;font-size:.72rem;cursor:pointer;border:1px solid #666;font-family:inherit;background:none;color:#fff;border-radius:6px}
  .ab-btn-ok{background:#fff;color:var(--ink);border-color:#fff}
  .ab-btn-ok:hover{background:var(--tint)}
  .ab-btn-no:hover{background:rgba(255,255,255,.1)}
</style>
</head>
<body>
<!-- GENERATED by makeTipsPage.py - do not edit by hand. The tips live in the tool pages
     (RCW_TIPS, COMPLETENESS_TIPS, CONNECTIVITY_TIPS, and the retrievers' TIPS); the Spanish
     text lives in tipsTranslations.es.json. Edit those and re-run: python3 makeTipsPage.py -->
<div class="topbar">
  <div class="topbar-inner">
    <div class="topbar-brand">
      <a href="https://metadatagamechangers.com" target="_blank" rel="noopener">
        <img class="brand-logo" src="https://images.squarespace-cdn.com/content/v1/52ffa419e4b05b374032e6d9/1577498408185-9LMHCVUJMNL2UBCIUOB9/Metadata+Game+Changers+Logo-Light.png?format=300w" alt="Metadata Game Changers" onerror="this.style.display='none'" />
      </a>
      <div class="brand-title-wrap"><div class="brand-tool-name">[[BRAND]]</div></div>
    </div>
    <div class="topbar-links">
      [[TOPBAR]]
    </div>
  </div>
</div>

<div class="wrap">
  <p class="intro">[[INTRO]]</p>
'''

PAGE_FOOT = '''
  <footer>
    [[FOOTER]]
  </footer>
</div>
<!-- Google Analytics (shared consent with the rest of the suite via localStorage 'rcw-ga') -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-9JQRWY72HW"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  try{ if(localStorage.getItem('rcw-ga')==='declined') window['ga-disable-G-9JQRWY72HW']=true; }catch(e){}
  gtag('js', new Date());
  gtag('config', 'G-9JQRWY72HW');
</script>
<!-- Analytics consent banner -->
<div id="analytics-banner">
  <span>[[BANNER]]</span>
  <div id="analytics-banner-btns">
    <button class="ab-btn ab-btn-ok" type="button" onclick="hideBanner('accepted')">[[BANNER_OK]]</button>
    <button class="ab-btn ab-btn-no" type="button" onclick="hideBanner('declined')">[[BANNER_NO]]</button>
  </div>
</div>
<script>
  function hideBanner(choice){
    try{ localStorage.setItem('rcw-ga', choice); }catch(e){}
    document.getElementById('analytics-banner').style.display='none';
    if (choice === 'declined') window['ga-disable-G-9JQRWY72HW'] = true;
  }
  (function(){
    var choice=null; try{ choice=localStorage.getItem('rcw-ga'); }catch(e){}
    if (choice) document.getElementById('analytics-banner').style.display='none';
    if (choice === 'declined') window['ga-disable-G-9JQRWY72HW'] = true;
  })();
</script>
</body>
</html>
'''


def fill(template, tokens):
    for k, v in tokens.items():
        template = template.replace(f"[[{k}]]", v)
    leftover = re.findall(r"\[\[[A-Z_]+\]\]", template)
    if leftover:
        sys.exit(f"ERROR: unfilled template tokens: {leftover}")
    return template


def footer_html(collected, L):
    links = [f'<a href="{fname}">{html.escape(name)}</a>' for fname, name, _ in collected]
    listed = ", ".join(links[:-1]) + f",\n    {L['foot_and']} " + links[-1] + "."
    return f"{L['foot_lede']}\n    {listed}\n    {L['foot_tail']}"


def render(collected, L):
    head = fill(PAGE_HEAD, {"LANG": L["lang"], "TITLE": L["title"], "DESC": L["desc"],
                            "BRAND": L["brand"], "TOPBAR": L["topbar"], "INTRO": L["intro"]})
    foot = fill(PAGE_FOOT, {"FOOTER": footer_html(collected, L), "BANNER": L["banner"],
                            "BANNER_OK": L["banner_ok"], "BANNER_NO": L["banner_no"]})
    body = []
    # jump line: one link per tool section (anchor = tool filename sans .html, identical in
    # both languages; the tools' "Metadata Tips" nav links deep-link to these,
    # e.g. tips.html#orcidRetriever)
    jumps = " · ".join(
        f'<a href="#{fname.removesuffix(".html")}">{html.escape(name)}</a>'
        for fname, name, _ in collected
    )
    body.append(f'  <nav class="jump">{L["jump"]} {jumps}</nav>')
    for fname, name, tips in collected:
        anchor = fname.removesuffix(".html")
        body.append(
            f'  <div class="tool-group" id="{anchor}">{html.escape(name)} <a class="open-tool" href="{fname}">{L["open_tool"]}</a>'
            f'<span class="count">{len(tips)} {L["tips_word"]}</span></div>'
        )
        body.append('  <div class="tips-grid">')
        for label, text, link in tips:
            if link:
                attrs = ' target="_blank" rel="noopener"' if link.startswith("http") else ""
                link_html = f'\n      <a class="tips-link" href="{html.escape(link)}"{attrs}>{L["learn_more"]}</a>'
            else:
                link_html = ""
            body.append(
                '    <div class="tip">\n      <div class="tips-label">' + label
                + '</div>\n      <div class="tips-text">' + text + '</div>' + link_html + '\n    </div>'
            )
        body.append('  </div>')
    return head + "\n".join(body) + foot


def main():
    collected = collect()
    translations = json.load(open(TRANSLATIONS_FILE, encoding="utf-8"))
    es_collected, missing = translate(collected, translations)
    for m in missing:
        print(f"WARNING: no Spanish translation for {m} — English text used", file=sys.stderr)
    pages = {LANGS["en"]["out"]: render(collected, LANGS["en"]),
             LANGS["es"]["out"]: render(es_collected, LANGS["es"])}
    total = sum(len(t[2]) for t in collected)
    if "--check" in sys.argv:
        stale = [f for f, page in pages.items()
                 if open(f, encoding="utf-8").read() != page]
        if stale or missing:
            sys.exit(f"STALE or missing translations — re-run: python3 makeTipsPage.py  "
                     f"(stale: {stale or 'none'}; missing translations: {len(missing)})")
        print(f"tips.html and tips.es.html are up to date ({total} tips).")
    else:
        for f, page in pages.items():
            open(f, "w", encoding="utf-8").write(page)
        print(f"tips.html + tips.es.html written — {total} tips from {len(collected)} tools"
              f"{f', {len(missing)} untranslated' if missing else ''}.")


if __name__ == "__main__":
    main()
