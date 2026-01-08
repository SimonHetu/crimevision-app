from peewee import fn # Import de fonctions SQL
from typing import List, Dict # Types utilisés pour documenter les valeurs retournées
from crimevision.core.db.database import get_db # Permet d'obtenir la connexion active à la base de données
from crimevision.core.db.models.user import User # Modèle Peewee représentant la table des utilisateurs
import datetime # Utilisé pour gérer les dates de création et de mise à jour
import bcrypt # Import de bcrypt pour le hachage des mots de passe


# Service responsable de toute la logique métier liée aux utilisateurs
# (création, modification, suppression, sécurité, statistiques)
class UserService:

    # Vérifie que bcrypt est bien installé avant toute opération sensible
    def _require_bcrypt(self):
        if not bcrypt:
            raise RuntimeError("bcrypt n'est pas installé. Exécutez: uv add bcrypt")

    # Transforme un mot de passe en hash sécurisé avant stockage en db
    def _hash_password(self, password: str) -> str:
        self._require_bcrypt()
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # Récupère une liste d'utilisateurs avec une limite configurable
    def list_users(self, limit: int = 50) -> List[Dict]:
        db = get_db()
        with db.connection_context():
            q = User.select().order_by(User.id).limit(limit)
            return [
                {
                    "id": u.id,
                    "email": u.email,
                    "name": u.name,
                    "pseudo": u.pseudo,
                    "createdAt": getattr(u, "createdAt", None),
                    "updatedAt": getattr(u, "updatedAt", None),
                }
                for u in q
            ]

    # Crée un nouvel utilisateur en enregistrant un mot de passe haché
    def create_user(self, *, email: str, name: str, pseudo: str, password: str) -> None:
        db = get_db()
        with db.connection_context():
            hashed = self._hash_password(password)
            User.create(email=email, name=name, pseudo=pseudo, hashedPassword=hashed)

    # Met à jour les informations d'un utilisateur existant
    # Le mot de passe est mis à jour uniquement s'il est fourni
    def update_user(self, user_id: int, *, email: str, name: str, pseudo: str, password=None):
        data = {
            "email": email,
            "name": name,
            "pseudo": pseudo,
            "updatedAt": datetime.datetime.utcnow(),
        }

        # Si un nouveau mot de passe est fourni, il est re-haché
        if password:
            data["hashedPassword"] = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

        return User.update(**data).where(User.id == user_id).execute()


    # Supprime définitivement un utilisateur de la base de données
    def delete_user(self, user_id: int) -> None:
        db = get_db()
        with db.connection_context():
            User.delete().where(User.id == user_id).execute()

    # Retourne le nombre total d'utilisateurs enregistrés
    def count_users(self) -> int:
        return User.select(fn.COUNT(User.id)).scalar() or 0


    # Retourne les utilisateurs les plus récents
    # Priorise la date de création si elle existe, sinon l'identifiant   
    def list_recent_users(self, limit: int = 10) -> List[Dict]:
        q = (
            User.select()
            .order_by(getattr(User, "createdAt", User.id).desc())
            .limit(limit)
        )
        return [
            {
                "id": u.id,
                "email": u.email,
                "name": u.name,
                "pseudo": getattr(u, "pseudo", ""),
                "createdAt": getattr(u, "createdAt", None),
            }
            for u in q
        ]
