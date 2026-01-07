import os
from peewee import DatabaseProxy
from playhouse.db_url import connect

db_proxy = DatabaseProxy()

def init_db(db_url: str | None = None):
    """
    Initialize the peewee database (once).
    Call this AFTER load_dotenv() in main().
    """
    if not db_url:
        db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        raise RuntimeError("DATABASE_URL missing")

    db = connect(db_url)
    db_proxy.initialize(db)
    return db

def get_db():
    """
    Return the initialized database.
    """
    db = db_proxy.obj
    if db is None:
        raise RuntimeError("DB not initialized. Call init_db() first.")
    return db

def close_db():
    db = get_db()
    if not db.is_closed():
        db.close()
