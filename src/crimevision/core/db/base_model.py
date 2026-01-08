from peewee import Model
from crimevision.core.db.database import db_proxy

# Modèle de base commun à toutes les entités de la base de données
# pour centraliser la configuration de connexion à la base de donnée
class BaseModel(Model):
    class Meta:
        database = db_proxy
