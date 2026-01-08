# 🧿 CrimeVision 🧿 (Desktop App)

CrimeVision est une application desktop (PySide6) qui permet de visualiser et explorer des données criminelles (incidents), des postes de quartier (PDQ) et des utilisateurs.

---

## ✨ Fonctionnalités

- **Dashboard** : KPIs (total incidents, 7 jours, nombre de PDQs, users), tableaux récents, classements (Top PDQs / catégories).
- **Incidents** : filtres (PDQ, période, type, recherche, limite), tableau complet, copie rapide, suppression (optionnelle).
- **PDQs** : liste + recherche (lecture seule).
- **Users** : listing + statistiques.

---

## 🧰 Prérequis

- **Python 3.12+**
- **uv** installé (https://docs.astral.sh/uv/)

---

## 📦 Installation (clone + dépendances)

### 1.Cloner le projet

git clone https://github.com/SimonHetu/crimevision-app.git
cd crimevision-app


### 2.Installation des dépendances avec UV 
uv sync

### 3.Création du fichier .env
cp .env.example .env

### 4.Remplir avec les informations de Neon
DATABASE_URL="postgresql://USER:PASSWORD@HOST:PORT/DBNAME"

### 5.Lancer l'application 
uv run crimevision-app


## 🗄 Requirement.txt
Le fichier requirements.txt a été généré à partir de l’environnement virtuel avec uv pip freeze garantissant que les dépendances nécessaires pour exécuter l’application sont listées.
