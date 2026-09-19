"""Hook MkDocs du catalogue d'API.

Chaque API est un fichier Markdown de ``docs/apis/`` doté d'un en-tête YAML
(voir ``docs/contribuer.md``). À partir de ces fichiers, le hook :

* construit automatiquement la navigation (thèmes et API) ;
* génère une page par thème (``themes/<slug>/``) ;
* remplace les marqueurs suivants dans les pages Markdown :
    ``<!-- catalogue -->``            catalogue complet (filtres à gauche + tuiles DSFR)
    ``<!-- catalogue:<theme> -->``    catalogue restreint à un thème
    ``<!-- statistiques -->``         nombre d'API ouvertes / avec authentification
    ``<!-- feuille-de-route -->``     feuille de route (mermaid gitGraph + tableau)
    ``<!-- plan-du-site -->``         plan du site
* enrichit chaque fiche d'API : fiche d'identité, contact du producteur et
  documentation OpenAPI rendue avec Redoc (fichier local ou URL) ;
* publie une page Redoc plein écran par API (``redoc/<slug>.html``) ;
* vérifie la complétude de chaque fiche (avertissements bloquants en ``--strict``).
"""

from __future__ import annotations

import html
import logging
import re
from datetime import date
from pathlib import Path

import yaml
from mkdocs.structure.files import File
from mkdocs.utils import get_relative_url
from mkdocs.utils.meta import get_data

log = logging.getLogger("mkdocs.hooks.catalogue")

META_REQUISES = ["title", "resume", "theme", "acces", "statut", "version", "producteur", "openapi"]
SECTIONS_REQUISES = [
    "Description fonctionnelle",
    "Présentation",
    "Cas d'usage",
    "Modalités d'accès",
    "Évolutions du produit",
]
PERIODES = {"seconde": 1, "minute": 60, "heure": 3600, "jour": 86400}
MOIS = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]

STATE: dict = {"apis": [], "cfg": {}, "roadmap": [], "root": Path("."), "stash": {}, "md": None}


def _stash(page, fragment: str) -> str:
    """Met de côté un fragment HTML : il est réinjecté tel quel après le rendu Markdown
    (évite que le HTML complexe soit réinterprété par le moteur Markdown)."""
    token = f"CATALOGUEFRAGMENT{len(STATE['stash'])}X"
    STATE["stash"][token] = fragment
    return f"\n\n{token}\n\n"


def _markdown(texte: str) -> str:
    """Convertit du Markdown avec les extensions du site (tuiles DSFR comprises)."""
    md = STATE["md"]
    if md is None:
        import markdown as _md
        conf = STATE["config"]
        md = STATE["md"] = _md.Markdown(extensions=conf.markdown_extensions,
                                        extension_configs=conf.mdx_configs)
    md.reset()
    return md.convert(texte)


# ---------------------------------------------------------------------------
# Chargement des données
# ---------------------------------------------------------------------------
def _is_url(value: str) -> bool:
    return bool(re.match(r"^https?://", str(value or "")))


def _as_list(value) -> list:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _load_apis(docs_dir: Path, cfg: dict) -> list[dict]:
    apis = []
    for path in sorted((docs_dir / "apis").glob("*.md")):
        source = path.read_text(encoding="utf-8")
        body, meta = get_data(source)
        slug = path.stem
        acces = _as_list(meta.get("acces"))
        api = {
            "slug": slug,
            "src_uri": f"apis/{path.name}",
            "meta": meta,
            "body": body,
            "title": meta.get("title", slug),
            "themes": _as_list(meta.get("theme")),
            "acces": acces,
            "ouverte": bool(acces) and all(cfg["acces"].get(a, {}).get("ouverte") for a in acces),
            "statut": meta.get("statut", "production"),
        }
        _validate(api, cfg)
        apis.append(api)
    return sorted(apis, key=lambda a: a["title"].lower())


def _validate(api: dict, cfg: dict) -> None:
    where = api["src_uri"]
    for key in META_REQUISES:
        if not api["meta"].get(key):
            log.warning("%s : métadonnée obligatoire manquante « %s »", where, key)
    for theme in api["themes"]:
        if theme not in cfg["themes"]:
            log.warning("%s : thème inconnu « %s » (voir extra.catalogue.themes)", where, theme)
    for mode in api["acces"]:
        if mode not in cfg["acces"]:
            log.warning("%s : modalité d'accès inconnue « %s »", where, mode)
    if api["statut"] not in cfg["statuts"]:
        log.warning("%s : statut inconnu « %s »", where, api["statut"])
    producteur = api["meta"].get("producteur") or {}
    if not producteur.get("contact"):
        log.warning("%s : le contact du producteur est obligatoire (producteur.contact)", where)
    if "quota" not in api["meta"]:
        log.warning("%s : quota d'appels manquant (quota.requetes + quota.periode, ou « non communiqué »)", where)
    elif isinstance(api["meta"]["quota"], dict):
        q = api["meta"]["quota"]
        if not isinstance(q.get("requetes"), int) or q.get("periode") not in PERIODES:
            log.warning("%s : quota invalide (requetes entier, periode parmi %s)", where, ", ".join(PERIODES))
    titres = [t.strip() for t in re.findall(r"^##\s+(.+)$", api["body"], flags=re.M)]
    for section in SECTIONS_REQUISES:
        if not any(t.startswith(section) for t in titres):
            log.warning("%s : section obligatoire manquante « ## %s »", where, section)


# ---------------------------------------------------------------------------
# Événements MkDocs
# ---------------------------------------------------------------------------
def on_config(config, **kwargs):
    cfg = config.extra.get("catalogue", {})
    cfg.setdefault("themes", {})
    cfg.setdefault("acces", {})
    cfg.setdefault("statuts", {})
    root = Path(config.config_file_path).parent
    docs_dir = Path(config.docs_dir)
    STATE["cfg"] = cfg
    STATE["root"] = root
    STATE["stash"] = {}
    STATE["config"] = config
    STATE["md"] = None
    STATE["apis"] = _load_apis(docs_dir, cfg)

    roadmap_file = root / cfg.get("feuille_de_route", "data/feuille_de_route.yml")
    STATE["roadmap"] = yaml.safe_load(roadmap_file.read_text(encoding="utf-8")) if roadmap_file.exists() else []

    # Navigation générée automatiquement
    themes_utilises = [t for t in cfg["themes"] if any(t in a["themes"] for a in STATE["apis"])]
    config["nav"] = [
        {"Catalogue": "index.md"},
        {"Thèmes": [{cfg["themes"][t]["libelle"]: f"themes/{t}.md"} for t in themes_utilises]},
        {"API": [{a["title"]: a["src_uri"]} for a in STATE["apis"]]},
        {"Feuille de route": "feuille-de-route.md"},
        {"Publier une API": "contribuer.md"},
    ]
    return config


def on_files(files, config, **kwargs):
    cfg = STATE["cfg"]
    for slug, theme in cfg["themes"].items():
        if not any(slug in a["themes"] for a in STATE["apis"]):
            continue
        content = (
            "---\n"
            f"title: {theme['libelle']}\n"
            "sidemenu: false\n"
            "---\n"
            f"# {theme['libelle']}\n\n"
            f"{theme.get('description', '')}\n\n"
            f"<!-- catalogue:{slug} -->\n"
        )
        files.append(File.generated(config, f"themes/{slug}.md", content=content))
    return files


def on_page_markdown(markdown, page, config, files, **kwargs):
    src = page.file.src_uri
    api = next((a for a in STATE["apis"] if a["src_uri"] == src), None)
    if api:
        markdown = _enrich_api_page(markdown, api, page)

    markdown = re.sub(
        r"<!-- catalogue(?::([\w-]+))? -->",
        lambda m: _stash(page, _render_catalogue(page, m.group(1))),
        markdown,
    )
    markdown = markdown.replace("<!-- statistiques -->", _stash(page, _render_stats(STATE["apis"])))
    markdown = markdown.replace("<!-- feuille-de-route -->", _stash(page, _render_roadmap(page)))
    markdown = markdown.replace("<!-- plan-du-site -->", _render_plan(page))
    return markdown


def on_page_content(html_content, page, config, files, **kwargs):
    for token, fragment in STATE["stash"].items():
        if token in html_content:
            html_content = html_content.replace(f"<p>{token}</p>", fragment).replace(token, fragment)
    aside = STATE.get("asides", {}).get(page.file.src_uri)
    if aside:
        coupure = html_content.find('<h2 id="specification-openapi"')
        if coupure == -1:
            coupure = len(html_content)
        html_content = (
            '<div class="fr-grid-row fr-grid-row--gutters api-page">'
            f'<div class="fr-col-12 fr-col-lg-8 api-page__contenu">{html_content[:coupure]}</div>'
            f'<div class="fr-col-12 fr-col-lg-4">{aside}</div>'
            "</div>" + html_content[coupure:]
        )
    return html_content


def on_post_build(config, **kwargs):
    """Pages Redoc plein écran : site/redoc/<slug>.html."""
    out = Path(config.site_dir) / "redoc"
    out.mkdir(parents=True, exist_ok=True)
    for api in STATE["apis"]:
        spec = api["meta"].get("openapi")
        if not spec:
            continue
        spec_url = spec if _is_url(spec) else f"../{spec}"
        fallback = api["meta"].get("openapi_local", "")
        fallback = f"../{fallback}" if fallback else ""
        titre = html.escape(api["title"])
        (out / f"{api['slug']}.html").write_text(
            f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{titre} – Documentation OpenAPI</title>
  <style>body{{margin:0}} .retour{{display:block;padding:.75rem 1.5rem;font-family:Marianne,arial,sans-serif;background:#000091;color:#fff}}</style>
</head>
<body>
  <a class="retour" href="../apis/{api['slug']}/">Retour à la fiche {titre}</a>
  <div id="redoc" data-spec-url="{html.escape(spec_url)}" data-fallback-url="{html.escape(fallback)}"></div>
  <script src="../assets/vendor/redoc.standalone.js"></script>
  <script src="../assets/js/catalogue.js"></script>
</body>
</html>
""",
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# Rendus
# ---------------------------------------------------------------------------
def _url(page, target: str) -> str:
    """URL relative à la page (pour le HTML brut, non traité par MkDocs)."""
    return get_relative_url(target, page.url)


def _lien(page, src_uri: str) -> str:
    """Lien vers un fichier source .md (résolu et vérifié par MkDocs)."""
    return get_relative_url(src_uri, page.file.src_uri)


def _badge_acces(api: dict) -> str:
    return "API ouverte|success" if api["ouverte"] else "Accès contrôlé|warning"


def _theme_label(slug: str) -> str:
    return STATE["cfg"]["themes"].get(slug, {}).get("libelle", slug)


def _tile(api: dict, page) -> str:
    cfg = STATE["cfg"]
    theme = api["themes"][0] if api["themes"] else ""
    picto = api["meta"].get("picto") or cfg["themes"].get(theme, {}).get("picto", "digital/coding")
    statut = cfg["statuts"].get(api["statut"], {}).get("libelle", api["statut"])
    themes = ", ".join(_theme_label(t) for t in api["themes"])
    resume = str(api["meta"].get("resume", "")).replace("\n", " ").strip()
    recherche = " ".join([api["title"], resume, themes, " ".join(api["meta"].get("mots_cles", []) or [])]).lower()
    return f"""
<div class="fr-col-12 fr-col-md-6 fr-col-xl-4 api-item" data-themes="{' '.join(api['themes'])}" data-acces="{' '.join(api['acces'])}" data-ouverte="{str(api['ouverte']).lower()}" data-statut="{api['statut']}" data-recherche="{html.escape(recherche)}" markdown="1">

/// tile | {api['title']}
    target: {_url(page, "apis/" + api["slug"] + "/")}
    description: {resume}
    badge: {_badge_acces(api)}
    picto: {picto}
    markup: h3
{themes}. {statut}, version {api['meta'].get('version', '')}
///

</div>
"""


def _render_stats(apis: list[dict]) -> str:
    cfg = STATE["cfg"]
    total = len(apis)
    ouvertes = sum(1 for a in apis if a["ouverte"])
    auth = total - ouvertes
    par_mode = []
    for slug, mode in cfg["acces"].items():
        if mode.get("ouverte"):
            continue
        n = sum(1 for a in apis if slug in a["acces"])
        if n:
            par_mode.append(f'{mode["libelle"]} : <span data-stat-mode="{slug}">{n}</span>')
    detail = " ; ".join(par_mode)
    return f"""
<div class="catalogue-stats" role="group" aria-label="Répartition des API par modalité d'accès">
  <p class="catalogue-stats__item"><span class="catalogue-stats__nombre" data-stat="total">{total}</span> API au catalogue</p>
  <p class="catalogue-stats__item catalogue-stats__item--ouverte"><span class="catalogue-stats__nombre" data-stat="ouvertes">{ouvertes}</span> API ouvertes, sans authentification</p>
  <p class="catalogue-stats__item catalogue-stats__item--auth"><span class="catalogue-stats__nombre" data-stat="auth">{auth}</span> API soumises à contrôle d'accès</p>
</div>
<p class="fr-text--sm fr-mb-4w">Mécanismes d'authentification (une API peut en proposer plusieurs) : {detail}.</p>
"""


def _checkbox(name: str, value: str, label: str, count: int) -> str:
    ident = f"filtre-{name}-{value}"
    return f"""<div class="fr-fieldset__element"><div class="fr-checkbox-group fr-checkbox-group--sm">
<input type="checkbox" id="{ident}" name="{name}" value="{value}">
<label class="fr-label" for="{ident}">{html.escape(label)} ({count})</label>
</div></div>"""


def _render_sidebar(page, apis: list[dict], theme_actif: str | None) -> str:
    cfg = STATE["cfg"]
    themes = []
    lien_tous = _url(page, "")
    courant = ' aria-current="page"' if theme_actif is None else ""
    classe = "fr-sidemenu__item fr-sidemenu__item--active" if theme_actif is None else "fr-sidemenu__item"
    total = len(STATE["apis"])
    themes.append(
        f'<li class="{classe}"><a class="fr-sidemenu__link" href="{lien_tous}"{courant}>Toutes les API ({total})</a></li>'
    )
    for slug, theme in cfg["themes"].items():
        n = sum(1 for a in STATE["apis"] if slug in a["themes"])
        if not n:
            continue
        actif = slug == theme_actif
        classe = "fr-sidemenu__item fr-sidemenu__item--active" if actif else "fr-sidemenu__item"
        aria = ' aria-current="page"' if actif else ""
        lien = _url(page, "themes/" + slug + "/")
        libelle = html.escape(theme["libelle"])
        themes.append(
            f'<li class="{classe}"><a class="fr-sidemenu__link" href="{lien}"{aria}>{libelle} ({n})</a></li>'
        )

    acces = [
        _checkbox("acces", slug, mode["libelle"], sum(1 for a in apis if slug in a["acces"]))
        for slug, mode in cfg["acces"].items()
        if any(slug in a["acces"] for a in apis)
    ]
    statuts = [
        _checkbox("statut", slug, s["libelle"], sum(1 for a in apis if a["statut"] == slug))
        for slug, s in cfg["statuts"].items()
        if any(a["statut"] == slug for a in apis)
    ]
    return f"""
<nav class="fr-sidemenu catalogue-sidemenu" aria-labelledby="sidemenu-themes-titre">
<div class="fr-sidemenu__inner">
<button class="fr-sidemenu__btn" aria-controls="sidemenu-catalogue" aria-expanded="false">Thèmes et filtres</button>
<div class="fr-collapse" id="sidemenu-catalogue">
<p class="fr-sidemenu__title" id="sidemenu-themes-titre">Thèmes</p>
<ul class="fr-sidemenu__list">
{''.join(themes)}
</ul>
<form class="catalogue-filtres" id="catalogue-filtres" role="search" aria-label="Filtrer les API">
<p class="fr-sidemenu__title fr-mt-4w">Filtres</p>
<div class="fr-input-group">
<label class="fr-label" for="filtre-recherche">Rechercher une API
<span class="fr-hint-text">Nom, usage, mot-clé</span></label>
<input class="fr-input" type="search" id="filtre-recherche" name="recherche" autocomplete="off">
</div>
<fieldset class="fr-fieldset" id="fieldset-acces">
<legend class="fr-fieldset__legend fr-text--regular">Modalité d'accès</legend>
{''.join(acces)}
</fieldset>
<fieldset class="fr-fieldset" id="fieldset-statut">
<legend class="fr-fieldset__legend fr-text--regular">Statut</legend>
{''.join(statuts)}
</fieldset>
<button type="reset" class="fr-btn fr-btn--tertiary fr-btn--sm fr-icon-close-circle-line fr-btn--icon-left">Réinitialiser les filtres</button>
</form>
</div>
</div>
</nav>
"""


def _render_catalogue(page, theme: str | None) -> str:
    apis = [a for a in STATE["apis"] if theme is None or theme in a["themes"]]
    tuiles = _markdown("\n".join(_tile(a, page) for a in apis))
    feuille = ""
    if theme is None:
        feuille = f"""
<h2 id="feuille-de-route" class="fr-mt-6w">Feuille de route des nouvelles API</h2>
{_render_roadmap(page)}
"""
    return f"""
<div class="fr-grid-row fr-grid-row--gutters catalogue">
<div class="fr-col-12 fr-col-md-3">
{_render_sidebar(page, apis, theme)}
</div>
<div class="fr-col-12 fr-col-md-9">

{_render_stats(apis)}

<p class="catalogue-resultat" id="catalogue-resultat" aria-live="polite">{len(apis)} API affichées</p>

<div class="fr-grid-row fr-grid-row--gutters catalogue-tuiles" id="catalogue-tuiles">
{tuiles}
</div>

<div class="fr-alert fr-alert--info fr-alert--sm fr-mt-4w catalogue-vide" id="catalogue-vide" hidden>
<p>Aucune API ne correspond à ces filtres. Retirez un filtre ou modifiez votre recherche.</p>
</div>
{feuille}
</div>
</div>
"""


def _mois(value) -> str:
    d = value if isinstance(value, date) else date.fromisoformat(f"{value}-01" if len(str(value)) == 7 else str(value))
    return f"{MOIS[d.month - 1]} {d.year}"


def _render_roadmap(page) -> str:
    projets = STATE["roadmap"] or []
    if not projets:
        return "_Aucune nouvelle API n'est planifiée pour le moment._"

    # Événements triés chronologiquement pour entrelacer les branches du gitGraph
    events = []
    for i, p in enumerate(projets):
        branche = p.get("branche") or re.sub(r"[^a-z0-9-]", "-", p["api"].lower())
        for j, jalon in enumerate(p.get("jalons", [])):
            events.append((str(jalon["date"]), i, j, branche, p, jalon))
    events.sort(key=lambda e: (e[0], e[1], e[2]))

    lignes = [
        "%%{init: { 'gitGraph': { 'mainBranchName': 'catalogue', 'showCommitLabel': true, 'rotateCommitLabel': false } } }%%",
        "gitGraph TB:",
        f'  commit id: "Catalogue : {len(STATE["apis"])} API" tag: "{_mois(date.today())}"',
    ]
    ouvertes: set[str] = set()
    courante = "catalogue"
    for d, _i, _j, branche, projet, jalon in events:
        label = f"{jalon['libelle']} ({_mois(d)})".replace('"', "'")
        if jalon.get("mise_en_production"):
            if branche not in ouvertes:
                lignes += ["  checkout catalogue", f"  branch {branche}"]
                ouvertes.add(branche)
            lignes += [f"  checkout {branche}", f'  commit id: "{label}"', "  checkout catalogue",
                       f'  merge {branche} tag: "{projet["api"].replace(chr(34), chr(39))}"']
            courante = "catalogue"
            continue
        if branche not in ouvertes:
            if courante != "catalogue":
                lignes.append("  checkout catalogue")
            lignes.append(f"  branch {branche}")
            ouvertes.add(branche)
        else:
            lignes.append(f"  checkout {branche}")
        lignes.append(f'  commit id: "{label}"')
        courante = branche

    mermaid = "\n".join(lignes)
    mermaid_js = _url(page, "assets/vendor/mermaid.min.js")

    # Alternative textuelle (RGAA) : tableau équivalent au graphe
    rows = []
    cfg = STATE["cfg"]
    for p in projets:
        jalons = "<br>".join(f"{_mois(j['date'])} : {html.escape(j['libelle'])}" for j in p.get("jalons", []))
        acces = ", ".join(cfg["acces"].get(a, {}).get("libelle", a) for a in _as_list(p.get("acces")))
        rows.append(
            f"<tr><td><strong>{html.escape(p['api'])}</strong><br><span class=\"fr-text--sm\">"
            f"{html.escape(p.get('description', ''))}</span></td><td>{_theme_label(p.get('theme', ''))}</td>"
            f"<td>{acces}</td><td>{jalons}</td></tr>"
        )
    return f"""
<figure class="catalogue-roadmap" role="group" aria-labelledby="roadmap-legende">
<div class="mermaid">{html.escape(mermaid)}</div>
<script src="{mermaid_js}"></script>
<figcaption id="roadmap-legende" class="fr-text--sm">Chaque branche représente une nouvelle API en construction ; la fusion dans la branche « catalogue » correspond à sa mise en production. Le détail figure dans le tableau ci-dessous.</figcaption>
</figure>

<div class="fr-table fr-table--bordered catalogue-jalons">
<div class="fr-table__wrapper"><div class="fr-table__container"><div class="fr-table__content">
<table>
<caption>Jalons des nouvelles API</caption>
<thead><tr><th scope="col">API</th><th scope="col">Thème</th><th scope="col">Accès prévu</th><th scope="col">Jalons</th></tr></thead>
<tbody>{''.join(rows)}</tbody>
</table>
</div></div></div>
</div>
"""


def _render_plan(page) -> str:
    cfg = STATE["cfg"]
    lignes = [f"- [Catalogue]({_lien(page, 'index.md')})"]
    for slug, theme in cfg["themes"].items():
        apis = [a for a in STATE["apis"] if slug in a["themes"]]
        if not apis:
            continue
        lignes.append("- [{}]({})".format(theme["libelle"], _lien(page, "themes/" + slug + ".md")))
        lignes += ["    - [{}]({})".format(a["title"], _lien(page, a["src_uri"])) for a in apis]
    for titre, cible in [("Feuille de route", "feuille-de-route.md"), ("Publier une API", "contribuer.md"),
                         ("Accessibilité", "accessibilite.md"), ("Mentions légales", "mentions-legales.md")]:
        lignes.append(f"- [{titre}]({_lien(page, cible)})")
    return "\n".join(lignes)


# ---------------------------------------------------------------------------
# Fiche API
# ---------------------------------------------------------------------------
def _contact_html(producteur: dict) -> str:
    contact = str(producteur.get("contact", ""))
    if "@" in contact and not _is_url(contact):
        return f'<a href="mailto:{html.escape(contact)}">{html.escape(contact)}</a>'
    if _is_url(contact):
        return f'<a href="{html.escape(contact)}" target="_blank" rel="noopener">{html.escape(contact)}</a>'
    return html.escape(contact)


def _nombre(n: float) -> str:
    return f"{n:,.0f}".replace(",", "\u202f")


def _render_quota(api: dict) -> str:
    q = api["meta"].get("quota")
    if not isinstance(q, dict):
        return ('<p class="fr-text--sm fr-mb-0">Non communiqué par le producteur. '
                "Contactez l'équipe avant un usage intensif.</p>")
    n, periode = q["requetes"], q["periode"]
    pluriel = "s" if n > 1 else ""
    portee = html.escape(str(q.get("portee") or "par client"))
    lignes = [f'<p class="api-aside__quota"><span class="api-aside__quota-nombre">{_nombre(n)}</span> '
              f"appel{pluriel} par {periode}</p>",
              f'<p class="fr-text--sm fr-mb-1v">{portee[:1].upper() + portee[1:]}'
              + (f", soit {_nombre(n * 60 / PERIODES[periode])} par minute" if periode == "seconde" else "")
              + (f", soit {_nombre(n / 60)} par seconde" if periode == "minute" and n >= 60 else "")
              + ".</p>"]
    if q.get("complement"):
        lignes.append(f'<p class="fr-text--sm fr-mb-1v">{html.escape(str(q["complement"]))}.</p>')
    lignes.append('<p class="fr-text--xs fr-mb-0 api-aside__mention">Au-delà, l\'API répond '
                  "<code>429 Too Many Requests</code>.</p>")
    return "".join(lignes)


def _render_aside(api: dict, page) -> str:
    cfg = STATE["cfg"]
    meta = api["meta"]
    producteur = meta.get("producteur") or {}
    spec = meta.get("openapi", "")
    spec_href = spec if _is_url(spec) else _url(page, spec)
    redoc_page = _url(page, "redoc/" + api["slug"] + ".html")

    if api["ouverte"]:
        statut_acces = ('<p class="fr-badge fr-badge--success">API ouverte</p>'
                        '<p class="fr-text--sm fr-mt-1w fr-mb-0">Aucune authentification : '
                        "l'API est librement accessible.</p>")
    else:
        statut_acces = ('<p class="fr-badge fr-badge--warning">Soumise à contrôle d\'accès</p>'
                        '<p class="fr-text--sm fr-mt-1w fr-mb-0">Un accès doit être obtenu auprès du producteur '
                        "avant tout appel.</p>")

    types = "".join(
        f'<li><strong>{html.escape(cfg["acces"].get(a, {}).get("libelle", a))}</strong>'
        f'<br><span class="fr-text--xs">{html.escape(cfg["acces"].get(a, {}).get("description", ""))}</span></li>'
        for a in api["acces"]
    )

    fichier = "" if _is_url(spec) else "OpenAPI"
    icone_contact = "fr-icon-links-line" if _is_url(producteur.get("contact", "")) else "fr-icon-mail-line"
    support = ""
    if producteur.get("support"):
        lien = html.escape(str(producteur["support"]))
        support = (f'<p class="fr-text--sm fr-mb-0">Support : <a href="{lien}" target="_blank" '
                   f'rel="noopener" title="{lien} - nouvelle fenêtre">{lien}</a></p>')

    return f"""
<aside class="api-aside" aria-label="Informations d'accès à l'API">
<section class="api-aside__bloc" aria-labelledby="aside-ouverture">
<h2 class="api-aside__titre" id="aside-ouverture">Ouverture</h2>
{statut_acces}
</section>
<section class="api-aside__bloc" aria-labelledby="aside-types">
<h2 class="api-aside__titre" id="aside-types">Types d'accès</h2>
<ul class="api-aside__liste">{types}</ul>
<p class="fr-text--xs fr-mb-0"><a href="#modalites-dacces">Détail des modalités d'accès</a></p>
</section>
<section class="api-aside__bloc" aria-labelledby="aside-swagger">
<h2 class="api-aside__titre" id="aside-swagger">Swagger de l'API</h2>
<p class="fr-text--sm fr-mb-1w">Spécification OpenAPI, version {html.escape(str(meta.get('version', '')))}.</p>
<ul class="fr-btns-group fr-btns-group--sm fr-btns-group--icon-left">
<li><a class="fr-btn fr-btn--sm fr-icon-code-s-slash-line" href="#specification-openapi">Consulter dans la page</a></li>
<li><a class="fr-btn fr-btn--sm fr-btn--secondary fr-icon-fullscreen-line" href="{redoc_page}">Ouvrir en pleine page</a></li>
<li data-preview-omit><a class="fr-btn fr-btn--sm fr-btn--tertiary fr-icon-file-download-line" href="{spec_href}">Fichier {fichier or 'OpenAPI (URL)'}</a></li>
</ul>
</section>
<section class="api-aside__bloc" aria-labelledby="aside-contact">
<h2 class="api-aside__titre" id="aside-contact">Contact du producteur</h2>
<p class="fr-text--sm fr-mb-0"><strong>{html.escape(str(producteur.get('nom', '')))}</strong></p>
<p class="fr-text--sm fr-mb-1w">{html.escape(str(producteur.get('equipe', '')))}</p>
<p class="fr-text--sm fr-mb-1v"><span class="{icone_contact} fr-icon--sm" aria-hidden="true"></span> {_contact_html(producteur)}</p>
{support}
</section>
<section class="api-aside__bloc" aria-labelledby="aside-quota">
<h2 class="api-aside__titre" id="aside-quota">Appels autorisés</h2>
{_render_quota(api)}
</section>
</aside>
"""


def _enrich_api_page(markdown: str, api: dict, page) -> str:
    cfg = STATE["cfg"]
    meta = api["meta"]
    producteur = meta.get("producteur") or {}
    statut = cfg["statuts"].get(api["statut"], {})
    spec = meta.get("openapi", "")
    spec_href = spec if _is_url(spec) else _url(page, spec)
    fallback = meta.get("openapi_local", "")
    fallback_href = _url(page, fallback) if fallback else ""

    statut_badge = statut.get("badge", "info")
    badges = [
        f'<li><p class="fr-badge fr-badge--{"success" if api["ouverte"] else "warning"}">'
        f'{"API ouverte" if api["ouverte"] else "Accès contrôlé"}</p></li>',
        f'<li><p class="fr-badge fr-badge--{statut_badge}">{statut.get("libelle", api["statut"])}</p></li>',
        f'<li><p class="fr-badge">Version {html.escape(str(meta.get("version", "")))}</p></li>',
    ]
    tags = "".join(
        f'<li><a class="fr-tag fr-tag--sm" href="{_url(page, f"themes/{t}/")}">{_theme_label(t)}</a></li>'
        for t in api["themes"]
    )
    redoc_page = _url(page, "redoc/" + api["slug"] + ".html")
    modes = ", ".join(cfg["acces"].get(a, {}).get("libelle", a) for a in api["acces"])
    demo = ""
    if meta.get("demonstration"):
        demo = (
            '<div class="fr-notice fr-notice--info fr-mb-2w"><div class="fr-container"><div class="fr-notice__body">'
            '<p class="fr-notice__title">Fiche de démonstration : cette API fictive illustre le fonctionnement '
            "du catalogue. Remplacez-la par vos propres API.</p></div></div></div>"
        )
    fiche = f"""
{demo}
<ul class="fr-badges-group">{''.join(badges)}</ul>
<ul class="fr-tags-group">{tags}</ul>

<div class="fr-callout api-fiche">
<p class="fr-callout__text">{html.escape(str(meta.get('resume', '')))}</p>
<dl class="api-fiche__liste">
<div><dt>Producteur</dt><dd>{html.escape(str(producteur.get('nom', '')))}</dd></div>
<div><dt>URL de base</dt><dd><code>{html.escape(str(meta.get('url_base', 'Non communiquée')))}</code></dd></div>
</dl>
</div>
"""

    contact = ""  # le contact figure désormais dans le panneau latéral droit
    STATE.setdefault("asides", {})[page.file.src_uri] = _render_aside(api, page)

    redoc_html = f"""
<p class="fr-text--sm">Source de la spécification : <a href="{spec_href}">{html.escape(spec)}</a>{' (copie locale utilisée si l’URL est indisponible)' if fallback else ''}.</p>

<div class="api-redoc">
<div class="api-redoc__viewer" data-spec-url="{spec_href}" data-fallback-url="{fallback_href}">
<p class="fr-text--sm">Chargement de la documentation OpenAPI…</p>
</div>
</div>
<script src="{_url(page, 'assets/vendor/redoc.standalone.js')}"></script>
"""
    redoc = "\n## Spécification OpenAPI { #specification-openapi }\n" + _stash(page, redoc_html)

    # Fiche d'identité juste après le titre H1
    if re.search(r"^# .+$", markdown, flags=re.M):
        markdown = re.sub(r"^(# .+)$", lambda m: m.group(1) + "\n" + _stash(page, fiche), markdown, count=1, flags=re.M)
    else:
        markdown = f"# {api['title']}\n{_stash(page, fiche)}\n{markdown}"

    markdown = markdown.replace("<!-- contact -->", contact)
    markdown = markdown.replace("<!-- openapi -->", redoc) if "<!-- openapi -->" in markdown else markdown + "\n" + redoc
    return markdown
