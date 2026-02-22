from __future__ import annotations

from peewee import fn  # Import de fonctions SQL
from typing import List, Dict, Optional  # Types utilisés pour documenter les valeurs retournées
from crimevision.core.db.database import get_db  # Permet d'obtenir la connexion active à la base de données
from crimevision.core.db.models.user import User  # Modèle Peewee représentant la table des utilisateurs
import datetime  # Utilisé pour gérer les dates de création et de mise à jour
import uuid
from typing import Dict

# Service responsable de toute la logique métier liée aux utilisateurs
# (liste, mise à jour, suppression, statistiques)
#
# IMPORTANT:
# - Clerk gère l'authentification (password/login/etc).
# - La DB sert surtout à stocker le mapping (clerkId, email) + role + données de profil.
class UserService:

    # Récupère une liste d'utilisateurs avec une limite configurable
    def list_users(self, limit: int = 50) -> List[Dict]:
        db = get_db()
        with db.connection_context():
            q = User.select().order_by(User.id).limit(limit)
            return [
                {
                    "id": u.id,
                    "clerkId": getattr(u, "clerkId", None),
                    "email": u.email,
                    "role": getattr(u, "role", None),
                    "createdAt": getattr(u, "createdAt", None),
                    "updatedAt": getattr(u, "updatedAt", None),
                }
                for u in q
            ]

    # Crée un "mirror user" dans la DB à partir des infos Clerk
    # (ex: quand un user se connecte pour la première fois)
    #
    # NOTE:
    # - Pas de mot de passe ici. Clerk s'en occupe.
    def upsert_user_from_clerk(
        self,
        *,
        clerk_id: str,
        email: Optional[str] = None,
        role: Optional[str] = None,
    ) -> Dict:
        db = get_db()
        with db.connection_context():
            now = datetime.datetime.utcnow()

            # Build defaults safely (do NOT set role unless provided)
            defaults: Dict[str, object] = {}

            if email is not None:
                defaults["email"] = email

            # IMPORTANT: leave role to DB default unless explicitly provided
            if role is not None:
                defaults["role"] = role

            if hasattr(User, "createdAt"):
                defaults["createdAt"] = now
            if hasattr(User, "updatedAt"):
                defaults["updatedAt"] = now

            user, created = User.get_or_create(
                clerkId=clerk_id,
                defaults=defaults,
            )

            # Update only provided fields (don't touch role unless provided)
            data: Dict[str, object] = {}
            if email is not None:
                data["email"] = email
            if role is not None:
                data["role"] = role
            if hasattr(User, "updatedAt"):
                data["updatedAt"] = now

            if data:
                User.update(**data).where(User.id == user.id).execute()
                user = User.get_by_id(user.id)

            return {
                "id": user.id,
                "clerkId": getattr(user, "clerkId", None),
                "email": user.email,
                "role": getattr(user, "role", None),
                "createdAt": getattr(user, "createdAt", None),
                "updatedAt": getattr(user, "updatedAt", None),
                "created": created,
            }

    # Met à jour les informations d'un utilisateur existant
    # (Admin panel: changer email et/ou role)
    def update_user(
        self,
        user_id: int,
        *,
        email: Optional[str] = None,
        role: Optional[str] = None,
    ) -> int:
        db = get_db()
        with db.connection_context():
            data = {}

            if email is not None:
                data["email"] = email
            if role is not None:
                data["role"] = role

            # updatedAt si la colonne existe
            if hasattr(User, "updatedAt"):
                data["updatedAt"] = datetime.datetime.utcnow()

            if not data:
                return 0  # rien à updater

            return User.update(**data).where(User.id == user_id).execute()
        
    def create_user(self, *, email: str, clerk_id: str | None = None) -> dict:
        if not clerk_id:
            clerk_id = f"manual_{uuid.uuid4().hex}"

        # role pas fourni → DB default (USER)
        return self.upsert_user_from_clerk(clerk_id=clerk_id, email=email)

    
    # Supprime définitivement un utilisateur de la base de données
    # NOTE: ça ne supprime PAS l'utilisateur côté Clerk (c'est un autre système).
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
        db = get_db()
        with db.connection_context():
            order_field = getattr(User, "createdAt", User.id)
            q = User.select().order_by(order_field.desc()).limit(limit)
            return [
                {
                    "id": u.id,
                    "clerkId": getattr(u, "clerkId", None),
                    "email": u.email,
                    "role": getattr(u, "role", None),
                    "createdAt": getattr(u, "createdAt", None),
                }
                for u in q
            ]
