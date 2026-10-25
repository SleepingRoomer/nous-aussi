#!/usr/bin/env python3
"""Génère le site statique « Malades » dans le dossier public/.

Usage :
    python3 build.py              # génère public/
    python3 build.py --apercu     # variante pour l'aperçu sur claude.ai (accueil sans <html>/<head>)

Les données sont dans data/ (maladies.json, personnes.json, frise.json),
les gabarits dans templates/, le CSS et le JavaScript dans static/.
"""
import json
import re
import shutil
import sys
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, StrictUndefined

ICI = Path(__file__).resolve().parent
SORTIE = ICI / "public"

DOMAINES = {
    "cinema": "Cinéma et scène",
    "musique": "Musique",
    "sport": "Sport",
    "sciences": "Sciences et techniques",
    "litterature": "Lettres et idées",
    "politique": "Politique",
}
STATUTS = ("declaree", "biographie", "hypothese")
PARTICULES = {"le", "la", "de", "du", "des", "van", "von", "der", "d'", "di", "da"}
ROMAINS = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
           (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]


def romain(n):
    out = ""
    for v, s in ROMAINS:
        while n >= v:
            out += s
            n -= v
    return out


def siecle(annee):
    s = (annee - 1) // 100 + 1
    return f"{romain(s)}{'er' if s == 1 else 'e'} siècle"


def initiales(nom):
    mots = [m for m in re.split(r"\s+", nom.strip()) if m]
    utiles = [m for m in mots if m.lower() not in PARTICULES and not re.fullmatch(r"[A-Z]\.", m)]
    if not utiles:
        utiles = mots
    if len(utiles) == 1:
        return utiles[0][0].upper()
    return (utiles[0][0] + utiles[-1][0]).upper()


def eclaircir(hexa, part=0.45):
    """Mélange une couleur avec du blanc (pour les dates sur fond sombre)."""
    hexa = hexa.lstrip("#")
    r, g, b = (int(hexa[i:i + 2], 16) for i in (0, 2, 4))
    r, g, b = (round(c + (255 - c) * part) for c in (r, g, b))
    return f"#{r:02X}{g:02X}{b:02X}"


def lower_first(s):
    return s[:1].lower() + s[1:] if s else s


def charger():
    maladies = json.loads((ICI / "data/maladies.json").read_text(encoding="utf-8"))
    personnes = json.loads((ICI / "data/personnes.json").read_text(encoding="utf-8"))
    frise = json.loads((ICI / "data/frise.json").read_text(encoding="utf-8"))
    par_slug = {m["slug"]: m for m in maladies}

    erreurs = []
    vus = set()
    for p in personnes:
        if p["slug"] in vus:
            erreurs.append(f"slug en double : {p['slug']}")
        vus.add(p["slug"])
        if p["domaine"] not in DOMAINES:
            erreurs.append(f"{p['slug']} : domaine inconnu « {p['domaine']} »")
        for l in p["maladies"]:
            if l["maladie"] not in par_slug:
                erreurs.append(f"{p['slug']} : maladie inconnue « {l['maladie']} »")
            if l["statut"] not in STATUTS:
                erreurs.append(f"{p['slug']} : statut inconnu « {l['statut']} »")
        # Règle éditoriale : pour une personne vivante, seule une maladie déclarée par elle-même est publiée.
        if p.get("deces") is None:
            for l in p["maladies"]:
                if l["statut"] != "declaree":
                    erreurs.append(f"{p['slug']} : personne vivante avec un statut « {l['statut']} » (seul « declaree » est publiable)")
    if erreurs:
        sys.exit("Données invalides :\n  - " + "\n  - ".join(erreurs))

    for p in personnes:
        p["vivant"] = p.get("deces") is None
        p["initiales"] = p.get("initiales") or initiales(p["nom"])
        p["annees"] = f"{p['naissance']} –" if p["vivant"] else f"{p['naissance']} – {p['deces']}"
        p["liens"] = p["maladies"]
        p["principale"] = p["maladies"][0]["maladie"]
        p["role_court"] = p["role"].split(",")[0]
        p.setdefault("lieu_naissance", None)

    ordre_statut = {s: i for i, s in enumerate(STATUTS)}
    for m in maladies:
        liste = [(p, l) for p in personnes for l in p["liens"] if l["maladie"] == m["slug"]]
        liste.sort(key=lambda pl: (ordre_statut[pl[1]["statut"]], not pl[0]["vivant"], pl[0]["nom"]))
        m["personnes"] = liste
        m["nb"] = len(liste)
        m.setdefault("rayures", False)
    return maladies, par_slug, personnes, frise


def css_maladies(maladies):
    regles = []
    for m in maladies:
        regles.append(
            f".m-{m['slug']}{{--c:{m['couleur']};--ink-c:{m['encre']};--t:{m['teinte']};--glow:{eclaircir(m['couleur'])}}}"
        )
        if m.get("rayures"):
            regles.append(f".m-{m['slug']} .mono,.mono.m-{m['slug']},.mhero.m-{m['slug']}{{background-image:repeating-linear-gradient(135deg,#E6E8EC 0 10px,#F4F5F7 10px 20px)}}")
            regles.append(f".m-{m['slug']} .mono,.mono.m-{m['slug']}{{color:{m['couleur']}}}")
    return "/* Généré par build.py à partir de data/maladies.json — ne pas modifier à la main */\n" + "\n".join(regles) + "\n"


def lignes_frise(frise, personnes, par_slug):
    evts = []
    for e in frise:
        evts.append({"type": "medecine", "annee": e["annee"], "ordre": 0, "maladie": e["maladie"],
                     "titre": e["titre"], "texte": e["texte"], "nom_maladie": par_slug[e["maladie"]]["court"]})
    for p in personnes:
        if p["vivant"]:
            continue
        for l in p["liens"]:
            evts.append({"type": "personne", "annee": p["deces"], "ordre": 1, "maladie": l["maladie"],
                         "statut": l["statut"], "p": p, "nom_maladie": par_slug[l["maladie"]]["court"]})
    evts.sort(key=lambda e: (e["annee"], e["ordre"]))
    lignes, dernier = [], None
    for e in evts:
        s = siecle(e["annee"])
        if s != dernier:
            lignes.append({"siecle": s})
            dernier = s
        lignes.append(e)
    return lignes


def construire(apercu=False):
    maladies, par_slug, personnes, frise = charger()
    env = Environment(loader=FileSystemLoader(ICI / "templates"), autoescape=True,
                      undefined=StrictUndefined, trim_blocks=True, lstrip_blocks=True)
    env.filters["lower_first"] = lower_first
    commun = {"maladies": maladies, "maladies_par_slug": par_slug, "domaines": DOMAINES,
              "fragment": False, "section": ""}

    if SORTIE.exists():
        shutil.rmtree(SORTIE)
    (SORTIE / "maladies").mkdir(parents=True)
    (SORTIE / "personnes").mkdir()
    shutil.copytree(ICI / "static", SORTIE / "static")
    (SORTIE / "static/maladies.css").write_text(css_maladies(maladies), encoding="utf-8")

    def ecrire(chemin, gabarit, **ctx):
        html = env.get_template(gabarit).render(**{**commun, **ctx})
        (SORTIE / chemin).write_text(html, encoding="utf-8")

    # Accueil
    une, deja = [], set()
    for m in maladies:
        for p, l in m["personnes"]:
            if l["statut"] == "declaree" and p["vivant"] and p["slug"] not in deja:
                une.append(p); deja.add(p["slug"]); break
    mosaique = (une + [p for p in personnes if p["slug"] not in deja])[:8]
    reperes = [{"annee": e["annee"], "maladie": e["maladie"], "court": e["titre"]} for e in sorted(frise, key=lambda e: e["annee"])]
    ressources, vus = [], set()
    for m in maladies:
        for r in m["ressources"]:
            if r["nom"] in vus:
                continue
            vus.add(r["nom"])
            ressources.append({**r, "pour": m["court"]})
    index_recherche = (
        [{"t": m["nom"], "s": f"{m['nb']} fiches", "k": m["court"], "u": f"maladies/{m['slug']}.html"} for m in maladies]
        + [{"t": p["nom"], "s": ", ".join(par_slug[l["maladie"]]["court"] for l in p["liens"]), "k": p["role"],
            "u": f"personnes/{p['slug']}.html"} for p in personnes]
    )
    ecrire("index.html", "index.html", root="", fragment=apercu, une=une, mosaique=mosaique,
           nb_personnes=len(personnes), reperes=reperes, ressources=ressources[:6],
           index_recherche=index_recherche)

    ecrire("frise.html", "frise.html", root="", section="frise", lignes=lignes_frise(frise, personnes, par_slug))
    ecrire("a-propos.html", "a-propos.html", root="", section="apropos")

    for m in maladies:
        ecrire(f"maladies/{m['slug']}.html", "maladie.html", root="../", section="maladies",
               m=m, personnes=m["personnes"])

    for p in personnes:
        mp = par_slug[p["principale"]]
        voisins = [q for q, _ in mp["personnes"] if q["slug"] != p["slug"]][:4]
        ecrire(f"personnes/{p['slug']}.html", "personne.html", root="../", section="maladies",
               p=p, voisins=voisins)

    nb = 3 + len(maladies) + len(personnes)
    print(f"{nb} pages générées dans {SORTIE.relative_to(ICI)}/")


if __name__ == "__main__":
    construire(apercu="--apercu" in sys.argv)
