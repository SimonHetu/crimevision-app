from typing import List, Dict
from crimevision.core.db.database import get_db
from crimevision.core.db.models.user import User
import datetime

try:
    import bcrypt
except ImportError:
    bcrypt = None


class UserService:
    def _require_bcrypt(self):
        if not bcrypt:
            raise RuntimeError("bcrypt not installed. Run: uv add bcrypt")

    def _hash_password(self, password: str) -> str:
        self._require_bcrypt()
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

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

    def create_user(self, *, email: str, name: str, pseudo: str, password: str) -> None:
        db = get_db()
        with db.connection_context():
            hashed = self._hash_password(password)
            User.create(email=email, name=name, pseudo=pseudo, hashedPassword=hashed)

    def update_user(self, user_id: int, *, email: str, name: str, pseudo: str, password=None):
        data = {
            "email": email,
            "name": name,
            "pseudo": pseudo,
            "updatedAt": datetime.datetime.utcnow(),
        }

        if password:
            data["hashedPassword"] = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

        return User.update(**data).where(User.id == user_id).execute()

    def delete_user(self, user_id: int) -> None:
        db = get_db()
        with db.connection_context():
            User.delete().where(User.id == user_id).execute()
