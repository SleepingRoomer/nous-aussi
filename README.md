# Malades

Site statique qui présente des personnalités ayant parlé publiquement de leur maladie, avec une page par maladie, une fiche par personne et une frise historique.

## Générer le site

Il faut Python 3.9 ou plus récent et Jinja2 :

```
pip install jinja2
python3 build.py
```

Le site complet est créé dans `public/`. Pour le regarder sur ton ordinateur :

```
cd public
python3 -m http.server 8000
```

puis ouvre http://localhost:8000 dans ton navigateur.

## Organisation

```
data/
  maladies.json    une entrée par maladie (couleurs, description, ressources)
  personnes.json   une entrée par personnalité
  frise.json       les dates où la médecine a décrit chaque maladie
templates/         gabarits HTML (Jinja2)
static/            style.css et app.js (recherche, filtres, frise)
build.py           génère public/ à partir des données et des gabarits
```

`static/maladies.css` est créé automatiquement à partir de `maladies.json` : il ne faut pas le modifier à la main.

## Ajouter une personnalité

Ajoute un bloc dans `data/personnes.json` :

```json
{
  "slug": "prenom-nom",
  "nom": "Prénom Nom",
  "role": "Métier",
  "naissance": 1970,
  "deces": null,
  "francophone": true,
  "domaine": "musique",
  "maladies": [{"maladie": "depression", "statut": "declaree", "annonce": 2019}],
  "resume": "Une ou deux phrases.",
  "parcours": [{"annee": 2019, "texte": "Ce qui s'est passé cette année-là."}],
  "citation": {"texte": "Ses propres mots.", "source": "Média, année"},
  "sources": [{"titre": "Titre de l'article, média, date", "url": "https://..."}]
}
```

- `deces` : `null` si la personne est en vie, sinon l'année.
- `domaine` : `cinema`, `musique`, `sport`, `sciences`, `litterature` ou `politique`.
- `maladie` : le `slug` d'une maladie de `maladies.json`.
- `statut` : `declaree` (la personne l'a dit elle-même), `biographie` (établi par des biographes) ou `hypothese` (diagnostic posé après coup).
- `initiales` (facultatif) : à préciser quand le calcul automatique se trompe, par exemple `"MD"` pour Marc Dal Maso.

Le script vérifie les données avant de générer le site. Il refuse notamment une personne vivante dont le statut n'est pas `declaree` : c'est la règle éditoriale du site.

## Ajouter une maladie

Ajoute un bloc dans `data/maladies.json` en reprenant la forme des autres (couleur du ruban, teinte claire, texte, ressources). La page, la carte de l'accueil, le filtre de la frise et les couleurs sont créés automatiquement.

## Mettre en ligne

Le dossier `public/` se dépose tel quel sur n'importe quel hébergeur de fichiers statiques :

- **Netlify** : glisse le dossier `public/` sur app.netlify.com/drop.
- **GitHub Pages** : publie le contenu de `public/` dans un dépôt et active Pages dans les réglages.

## À compléter avant la mise en ligne

- Vérifier chaque fiche et remplacer les textes entre crochets (`[CHIFFRE]`, `[Citation…]`, `[Texte de la fiche à rédiger]`).
- Ajouter les liens des associations dans `maladies.json` (champ `url`).
- Indiquer une adresse de contact dans `templates/a-propos.html`.
