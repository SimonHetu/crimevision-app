import os
from peewee import DatabaseProxy
from playhouse.db_url import connect

db_proxy = DatabaseProxy()

def init_db(db_url: str | None = None):
    """
    Initialise la base de donnée peewee
    """
    if not db_url:
        db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL manquante")

    db = connect(db_url)
    db_proxy.initialize(db)
    return db

def get_db():
    """
    Retourne la base de données initialisée
    """
    db = db_proxy.obj
    if db is None:
        raise RuntimeError("La base de donnée n'est pas initialisée")
    return db

def close_db():
    db = get_db()
    if not db.is_closed():
        db.close()
