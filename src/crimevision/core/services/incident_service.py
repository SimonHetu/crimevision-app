from typing import List, Dict, Optional
from datetime import datetime, timedelta

from peewee import fn

# Modèle Peewee représentant la table "Incident" en DB
from crimevision.core.db.models.incident import Incident


class IncidentService:

    """
    IncidentService
    ----------------
    Couche "service" entre l’interface (UI) et le modèle ORM (Incident).

    Rôle :
    - Centraliser toute la logique d’accès aux incidents
    - Encapsuler les requêtes SQL
    - Appliquer les filtres dynamiques
    - Retourner des données propres (dict) à l’interface
    """
    
    # =========================================================
    # LISTE D’INCIDENTS AVEC FILTRES
    # =========================================================
    def list_incidents(
        self,
        *,
        limit: int = 200,
        pdq_id: Optional[int] = None,
        period: str = "all",
        type_filter: str = "",
        search: str = "",
    ) -> List[Dict]:
        """
        Retourne une liste d’incidents avec filtres optionnels.
        """
        # Requête de base : tri par date décroissante + limite
        q = Incident.select().order_by(Incident.date.desc()).limit(limit)

        # -------------------------
        # Filtre PDQ
        # -------------------------
        if pdq_id is not None:
            q = q.where(Incident.pdqId == pdq_id)

        # -------------------------
        # Filtre période (24h / 7j / 30j)
        # -------------------------
        if period and period != "all":
            now = datetime.utcnow()
            if period == "day":
                start = now - timedelta(days=1)
            elif period == "week":
                start = now - timedelta(days=7)
            elif period == "month":
                start = now - timedelta(days=30)
            else:
                start = None
            if start:
                q = q.where(Incident.date >= start)

        # -------------------------
        # Filtre catégorie exacte
        # -------------------------
        if type_filter:
            q = q.where(fn.LOWER(Incident.category) == type_filter.strip().lower())

        # -------------------------
        # Recherche partielle
        # -------------------------
        if search:
            s = search.strip().lower()
            q = q.where(fn.LOWER(Incident.category).contains(s))

        # -------------------------
        # Transformation ORM -> dictionnaire
        # -------------------------
        return [
            {
                "id": i.id,
                "pdqId": i.pdqId,
                "category": i.category,
                "date": i.date,
                "timePeriod": i.timePeriod,
                "source": i.source,
                "sourceId": i.sourceId,
                "x": i.x,
                "y": i.y,
                "latitude": i.latitude,
                "longitude": i.longitude,
            }
            for i in q
        ]

    # =========================================================
    # SUPPRESSION
    # =========================================================
    def delete_incident(self, incident_id: int) -> None:
        """
        Supprime un incident par ID.
        """
        Incident.delete().where(Incident.id == incident_id).execute()

    # =========================================================
    # RÉCUPÉRATION PAR ID
    # =========================================================
    def get_incident_by_id(self, incident_id: int) -> Optional[Dict]:
        """
        Retourne un incident précis sous forme de dictionnaire.
        """
        i = Incident.get_or_none(Incident.id == incident_id)
        if not i:
            return None
        return {
            "id": i.id,
            "pdqId": i.pdqId,
            "category": i.category,
            "date": i.date,
            "timePeriod": i.timePeriod,
            "source": i.source,
            "sourceId": i.sourceId,
            "x": i.x,
            "y": i.y,
            "latitude": i.latitude,
            "longitude": i.longitude,
        }

    # =========================================================
    # COMPTE GLOBAL
    # =========================================================
    def count_all(self) -> int:
        """
        Nombre total d’incidents.
        """
        return Incident.select(fn.COUNT(Incident.id)).scalar() or 0


    def count_since_days(self, days: int) -> int:
        """
        Nombre d’incidents depuis X jours.
        """
        start = datetime.utcnow() - timedelta(days=days)
        return (
            Incident.select(fn.COUNT(Incident.id))
            .where(Incident.date >= start)
            .scalar()
            or 0
        )
    
    # =========================================================
    # PDQ UNIQUES
    # =========================================================
    def count_unique_pdqs(self) -> int:
        """
        Nombre de PDQs distincts présents en base.
        """
        q = (
            Incident.select(Incident.pdqId)
            .where(Incident.pdqId.is_null(False))
            .distinct()
        )
        return q.count()

    # =========================================================
    # CATÉGORIES DISTINCTES
    # =========================================================
    def list_categories(self) -> List[str]:

        """
        Retourne la liste des catégories distinctes (triées A-Z).
        """
        q = (
            Incident.select(Incident.category)
            .where(Incident.category.is_null(False))
            .distinct()
            .order_by(Incident.category.asc())
        )
        return [r.category for r in q if r.category]

    # =========================================================
    # TOP CATÉGORIES
    # =========================================================
    def top_categories(self, *, days: int = 30, limit: int = 10) -> List[Dict]:
        """
        Retourne les catégories les plus fréquentes
        sur les X derniers jours.
        """
        start = datetime.utcnow() - timedelta(days=days)
        q = (
            Incident.select(
                Incident.category.alias("category"),
                fn.COUNT(Incident.id).alias("count"),
            )
            .where(
                Incident.date.is_null(False),
                Incident.category.is_null(False),
                Incident.date >= start,
            )
            .group_by(Incident.category)
            .order_by(fn.COUNT(Incident.id).desc())
            .limit(limit)
        )
        return [{"category": r.category, "count": int(r.count)} for r in q]

    # =========================================================
    # TOP PDQS
    # =========================================================
    def top_pdqs(self, *, days: int = 30, limit: int = 10) -> List[Dict]:
        """
        Retourne les PDQs les plus actifs sur X jours.
        """
        start = datetime.utcnow() - timedelta(days=days)
        q = (
            Incident.select(
                Incident.pdqId.alias("pdqId"),
                fn.COUNT(Incident.id).alias("count"),
            )
            .where(
                Incident.date.is_null(False),
                Incident.pdqId.is_null(False),
                Incident.date >= start,
            )
            .group_by(Incident.pdqId)
            .order_by(fn.COUNT(Incident.id).desc())
            .limit(limit)
        )
        return [{"pdqId": int(r.pdqId), "count": int(r.count)} for r in q]

    # =========================================================
    # INCIDENTS PAR JOUR (POUR GRAPHIQUE)
    # =========================================================
    def count_by_day(self, *, days: int = 30, category: str | None = None) -> List[Dict]:
        """
        Retourne le nombre d’incidents par jour.

        Optionnel :
        - Filtrage par catégorie spécifique.
        """
        start = datetime.utcnow() - timedelta(days=days)

        # DATE_TRUNC coupe l'heure pour garder uniquement le jour
        day_expr = fn.DATE_TRUNC("day", Incident.date).alias("day")

        where = [
            Incident.date.is_null(False),
            Incident.date >= start,
        ]

        # Filtre catégorie si fourni
        if category:
            where.append(fn.LOWER(Incident.category) == category.strip().lower())

        q = (
            Incident.select(
                day_expr,
                fn.COUNT(Incident.id).alias("count"),
            )
            .where(*where)
            .group_by(day_expr)
            .order_by(day_expr)
        )

        # Transformation en liste exploitable par matplotlib
        out: List[Dict] = []
        for r in q:
            d = r.day
            day_str = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
            out.append({"day": day_str, "count": int(r.count)})
        return out