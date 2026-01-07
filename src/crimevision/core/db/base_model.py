from peewee import Model
from crimevision.core.db.database import db_proxy

class BaseModel(Model):
    class Meta:
        database = db_proxy
