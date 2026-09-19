"""Assemble le site MkDocs construit (./site) en un fichier HTML unique et autonome.

Usage : mkdocs build && python tools/bundle_preview.py [sortie.html]

Chaque page devient un <template> affiché par un routeur par ancre (#/chemin/).
CSS, polices, icônes, pictogrammes, JS DSFR et spécifications OpenAPI sont intégrés ;
Redoc et Mermaid sont chargés à la demande depuis cdn.jsdelivr.net (versions figées).
"""

from __future__ import annotations

import base64
import json
import posixpath
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "site"
DOCS = ROOT / "docs"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "catalogue-preview.html"

REDOC_CDN = "https://cdn.jsdelivr.net/npm/redoc@2.5.4/bundles/redoc.standalone.js"
MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@11.17.2/dist/mermaid.min.js"
MIME = {".woff2": "font/woff2", ".woff": "font/woff", ".svg": "image/svg+xml", ".png": "image/png"}
FONTS_KEEP = ("Marianne-Regular.", "Marianne-Medium.", "Marianne-Bold.", "Marianne-Light.", "Marianne-Regular_Italic.")


def data_uri(path: Path) -> str:
    return f"data:{MIME.get(path.suffix, 'application/octet-stream')};base64,{base64.b64encode(path.read_bytes()).decode()}"


def inline_css_urls(css: str, base: Path) -> str:
    def repl(m):
        url = m.group(1).strip("'\"")
        if url.startswith(("data:", "http", "#")):
            return m.group(0)
        target = (base / url.split("?")[0].split("#")[0]).resolve()
        if not target.exists():
            return m.group(0)
        if target.suffix in (".woff", ".ttf") or (target.suffix == ".woff2" and not target.name.startswith(FONTS_KEEP)):
            return "url(data:,)"  # polices non utilisées : ignorées (woff2 suffit)
        return f'url("{data_uri(target)}")'

    return re.sub(r"url\(([^)]+)\)", repl, css)


def filter_utility_css(css: str, used_classes: set[str]) -> str:
    """Ne garde que les règles d'icônes réellement utilisées (le fichier complet pèse plusieurs Mo en data URI)."""
    out = []
    for rule in re.findall(r"[^{}]+\{[^{}]*\}", css):
        selector = rule.split("{", 1)[0]
        classes = re.findall(r"\.(fr-(?:icon|fi)-[\w-]+)", selector)
        if classes and not any(c in used_classes for c in classes):
            continue
        out.append(rule)
    return "".join(out)


def page_key(html_path: Path) -> str:
    rel = html_path.relative_to(SITE).parent.as_posix()
    return "" if rel == "." else rel + "/"


def resolve(key: str, href: str) -> str | None:
    """Transforme un lien relatif en route (#/…) ; None si le lien doit être supprimé."""
    if href.startswith(("http:", "https:", "mailto:", "tel:", "#", "data:", "javascript:")):
        return href
    path = posixpath.normpath(posixpath.join(key or ".", href.split("#")[0]))
    frag = href.split("#", 1)[1] if "#" in href else ""
    path = "" if path == "." else path
    if path.startswith("redoc/") and path.endswith(".html"):
        return f"#/redoc/{Path(path).stem}/"
    if path.endswith("index.html"):
        path = path[: -len("index.html")]
    if Path(path).suffix and not path.endswith("/"):
        return None
    if path and not path.endswith("/"):
        path += "/"
    return f"#/{path}" + (f"::{frag}" if frag else "")


def rewrite_links(key: str, fragment: str) -> str:
    # Boutons de téléchargement (inertes dans une page publiée) : retirés
    fragment = re.sub(r"<li><a[^>]*\sdownload[^>]*>.*?</a></li>", "", fragment, flags=re.S)
    fragment = re.sub(r"<li data-preview-omit>.*?</li>", "", fragment, flags=re.S)
    # Scripts des bibliothèques : chargés à la demande par le routeur
    fragment = re.sub(r'<script src="[^"]*(?:redoc\.standalone|mermaid\.min)\.js"></script>', "", fragment)

    def repl(m):
        attr, quote, url = m.group(1), m.group(2), m.group(3)
        new = resolve(key, url)
        if new is None:
            return f"{attr}={quote}#{quote}"
        return f"{attr}={quote}{new}{quote}"

    return re.sub(r'\b(href)=(["\'])([^"\']*)\2', repl, fragment)


def main():
    pages: dict[str, dict] = {}
    for html_path in sorted(SITE.rglob("index.html")):
        key = page_key(html_path)
        if key.startswith(("search", "redoc")):
            continue
        html = html_path.read_text(encoding="utf-8")
        main_html = re.search(r'<main id="content" role="main">(.*?)</main>', html, re.S).group(1)
        title = re.search(r"<title>\s*(.*?)\s*</title>", html, re.S).group(1)
        title = re.sub(r"\s+", " ", title)
        main_html = rewrite_links(key, main_html)
        # Visionneuse Redoc : spécification intégrée (pas d'appel réseau)
        if key.startswith("apis/"):
            slug = key.split("/")[1]
            main_html = re.sub(r'data-spec-url="[^"]*"', f'data-spec-id="{slug}"', main_html)
            main_html = re.sub(r'data-fallback-url="[^"]*"', "", main_html)
        pages[key] = {"title": title, "html": main_html}

    index = (SITE / "index.html").read_text(encoding="utf-8")
    body = re.search(r"<body>(.*)</body>", index, re.S).group(1)
    before_main = body.split('<main id="content" role="main">')[0]
    after_main = body.split("</main>", 1)[1]
    after_main = re.split(r"<script", after_main, maxsplit=1)[0]
    chrome_top = rewrite_links("", before_main).replace('action="search.html"', 'id="preview-search"')
    chrome_bottom = rewrite_links("", after_main)
    chrome_top = chrome_top.replace('aria-current="page"', "")

    # Pictogrammes : sprite SVG interne
    all_html = chrome_top + chrome_bottom + "".join(p["html"] for p in pages.values())
    sprite = []
    seen = set()
    for m in re.finditer(r'href="[^"]*?/artwork/pictograms/([\w/-]+)\.svg#(artwork-[\w-]+)"', all_html):
        name = m.group(1)
        if name in seen:
            continue
        seen.add(name)
        svg = (SITE / "artwork" / "pictograms" / f"{name}.svg").read_text(encoding="utf-8")
        pid = "pic-" + name.replace("/", "-")
        for sym in re.findall(r"<symbol id=\"(artwork-[\w-]+)\">(.*?)</symbol>", svg, re.S):
            sprite.append(f'<symbol id="{pid}-{sym[0]}" viewBox="0 0 80 80">{sym[1]}</symbol>')

    def pic(m):
        return f'href="#pic-{m.group(1).replace("/", "-")}-{m.group(2)}"'

    for p in pages.values():
        p["html"] = re.sub(r'href="[^"]*?/artwork/pictograms/([\w/-]+)\.svg#(artwork-[\w-]+)"', pic, p["html"])

    used = set(re.findall(r"(fr-(?:icon|fi)-[\w-]+)", all_html))
    used |= {"fr-icon-arrow-right-line", "fr-icon-external-link-line", "fr-icon-arrow-up-fill", "fr-icon-mail-line",
             "fr-icon-close-line", "fr-icon-search-line", "fr-icon-menu-fill", "fr-icon-theme-fill", "fr-fi-theme-fill"}

    css = inline_css_urls((SITE / "dsfr.min.css").read_text(encoding="utf-8"), SITE)
    css += inline_css_urls(filter_utility_css((SITE / "utility/utility.min.css").read_text(encoding="utf-8"), used),
                           SITE / "utility")
    css += inline_css_urls((SITE / "css/theme.css").read_text(encoding="utf-8"), SITE / "css")
    css += (SITE / "assets/css/catalogue.css").read_text(encoding="utf-8")
    css += """
.api-redoc img[src*="redoc.ly"], .preview-redoc img[src*="redoc.ly"] { display: none; }
.preview-redoc-bar { padding: .75rem 1.5rem; background: var(--background-action-high-blue-france); }
.preview-redoc-bar a { color: #fff; }
"""

    # Spécifications OpenAPI intégrées en JSON
    specs = {}
    for md in sorted((DOCS / "apis").glob("*.md")):
        meta = yaml.safe_load(md.read_text(encoding="utf-8").split("---")[1])
        local = meta.get("openapi_local") or meta.get("openapi")
        if local and not str(local).startswith("http"):
            specs[md.stem] = {"title": meta["title"], "spec": yaml.safe_load((DOCS / local).read_text(encoding="utf-8"))}

    def safe(text: str) -> str:
        return text.replace("</script", "<\\/script").replace("<!--", "<\\!--")

    templates = "\n".join(
        f'<template id="tpl-{k.strip("/").replace("/", "--") or "accueil"}" data-title="{v["title"]}">{v["html"]}</template>'
        for k, v in pages.items()
    )
    dsfr_js = safe((SITE / "dsfr.module.min.js").read_text(encoding="utf-8"))
    app_js = safe((ROOT / "tools/preview_app.js").read_text(encoding="utf-8"))
    app_js = app_js.replace("__REDOC_CDN__", REDOC_CDN).replace("__MERMAID_CDN__", MERMAID_CDN)
    specs_json = safe(json.dumps(specs, ensure_ascii=False, separators=(",", ":"), default=str))

    out = f"""<!DOCTYPE html>
<html lang="fr" data-fr-scheme="system">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Catalogue des API</title>
<meta name="theme-color" content="#000091">
<style>{css}</style>
</head>
<body>
<svg xmlns="http://www.w3.org/2000/svg" style="display:none" aria-hidden="true">{''.join(sprite)}</svg>
{chrome_top}
<main id="content" role="main" tabindex="-1"></main>
{chrome_bottom}
{templates}
<script type="application/json" id="specs">{specs_json}</script>
<script type="module">{dsfr_js}</script>
<script>{app_js}</script>
</body>
</html>
"""
    OUT.write_text(out, encoding="utf-8")
    print(f"{OUT} : {OUT.stat().st_size / 1e6:.1f} Mo, {len(pages)} pages, {len(specs)} spécifications")


if __name__ == "__main__":
    main()
