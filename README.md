# 🧿 CrimeVision 🧿 (Desktop App)

CrimeVision est une application desktop (PySide6) qui permet de visualiser et explorer des données criminelles (incidents), des postes de quartier (PDQ) et des utilisateurs.

---

## ✨ Fonctionnalités

- **Dashboard** : KPIs (total incidents, 7 jours, nombre de PDQs, users), tableaux récents, classements (Top PDQs / catégories).
- **Stats** : graphique **incidents par jour** (7 / 30 / 90 jours), **Top catégories** (clic = filtre du graphique), **Top PDQs**.
- **Incidents** : filtres (PDQ, période, catégorie, limite), tableau complet, copie rapide, suppression (optionnelle).
- **PDQs** : liste + recherche (lecture seule).
- **Users** : listing + statistiques.
- **Imports** : exécution de scripts d’import backend (Incidents avec `--max`, Latest Incidents), logs intégrés + stop.

---

## 🧰 Prérequis

- **Python 3.12+**
- **uv** installé (https://docs.astral.sh/uv/)
- Une base PostgreSQL (ex: **Neon**)

---

## 📦 Installation (clone + dépendances)

### 1. Cloner le projet

git clone https://github.com/SimonHetu/crimevision-app.git  
cd crimevision-app

### 2. Installer les dépendances avec uv

uv sync

### 3. Créer le fichier .env

cp .env.example .env

### 4. Ajouter la connexion Neon

DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DBNAME"

### 5. Lancer l'application

uv run crimevision-app

---

## 🗄 requirements.txt

Le fichier `requirements.txt` est généré à partir de l’environnement virtuel via `uv pip freeze`, afin de lister les dépendances nécessaires à l’exécution de l’application.