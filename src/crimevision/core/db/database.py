import os
from peewee import OperationalError
from peewee import DatabaseProxy
from playhouse.db_url import connect

# Proxy global utilisé par tous les modèles Peewee de l’application
db_proxy = DatabaseProxy()


# Initialise la connexion à la base de données à partir de DATABASE_URL
def init_db(db_url: str | None = None):
    """
    Initialise la base de donnée peewee
    """

    # Récupère l’URL de la base depuis les variables d’environnement si non fournie
    if not db_url:
        db_url = os.environ.get("DATABASE_URL")
    
    # Empêche le démarrage de l’application si aucune base n’est configurée
    if not db_url:
        raise RuntimeError("DATABASE_URL manquante")

    # Connexion à la base de donnée
    db = connect(db_url)

    # Association de la connexion réelle au proxy Peewee
    db_proxy.initialize(db)
    return db

# Retourne une instance valide de la base de données


def get_db():
    """
    Retourne la base de données initialisée + s'assure qu'elle est vivante.
    (Neon peut dropper les connexions idle.)
    """
    db = db_proxy.obj
    if db is None:
        raise RuntimeError("La base de donnée n'est pas initialisée")

    try:
        if db.is_closed():
            db.connect(reuse_if_open=True)

        # Ping pour détecter une connexion zombie (idle drop)
        db.execute_sql("SELECT 1;")

    except Exception:
        # Si la connexion est morte, on ferme et on reconnecte proprement
        try:
            if not db.is_closed():
                db.close()
        except Exception:
            pass

        db.connect(reuse_if_open=True)

    return db

# Ferme proprement la connexion à la base lors de la fermeture de l’application
def close_db():
    db = get_db()
    if not db.is_closed():
        db.close()
