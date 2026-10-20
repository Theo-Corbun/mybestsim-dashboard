# MyBestSim - Dashboard d'Automatisation et d'Analyse eSIM

## 1. Presentation du projet

Ce projet repond a la Partie 1 (Data et Automatisation) du test technique MyBestSim. Il permet d'importer automatiquement les 18 fichiers CSV des fournisseurs de cartes eSIM, d'unifier et nettoyer les donnees, puis de generer un tableau de bord web interactif exposant l'ensemble des indicateurs financiers et volumetriques demandes.


## 2. Architecture modulaire par blocs de competences

Le code source est decoupe en modules independants au sein du dossier `modules/` afin de garantir une separation stricte des responsabilites :

```text
mybestsim-dashboard/
├── data/                      # Contient les 18 fichiers CSV des fournisseurs
├── modules/
│   ├── __init__.py            # Declaration du package Python
│   ├── parser.py              # Bloc 1 : Lecture dynamique, validation et nettoyage des CSV
│   ├── pricing.py             # Bloc 2 : Calculs financiers (min/max, moyenne, >100 EUR, cout/Go)
│   ├── datavolume.py          # Bloc 3 : Volumes de produits, moyenne de Go, gestion de l'illimite
│   └── visualization.py       # Bloc 4 : Tableaux agreges et graphiques par fournisseur
├── main.py                    # Point d'entree principal et interface Streamlit
├── requirements.txt           # Dependances Python
└── README.md                  # Documentation d'installation, de lancement et de maintenance

## 3. Lancement du projet

Windows

python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m streamlit run main.py

Explication : crée l'environnement, l'active, installe les dépendances puis lance le dashboard.

Linux / macOS

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 -m streamlit run main.py

Explication : crée l'environnement, l'active, installe les dépendances puis lance le dashboard.

Le dashboard sera disponible sur :

http://localhost:8501