from typing import List, Dict, Optional

# Utilisé pour calculer des périodes de temps (ex: 7 derniers jours)
from datetime import datetime, timedelta
from peewee import fn

# Modèle Peewee représentant la table Incident dans la base de données
from crimevision.core.db.models.incident import Incident

# Service responsable des requêtes et statistiques liées aux incidents (listing, filtres, KPIs, top)
class IncidentService:

    # Retourne une liste d’incidents avec filtres (pdq, période, catégorie/type, recherche) et limite
    def list_incidents(
        self,
        *,
        limit: int = 200,
        pdq_id: Optional[int] = None,
        period: str = "all",
        type_filter: str = "",
        search: str = "",
    ) -> List[Dict]:
        q = Incident.select().order_by(Incident.date.desc()).limit(limit)

        # Filtre par PDQ si un PDQ est sélectionné
        if pdq_id is not None:
            q = q.where(Incident.pdqId == pdq_id)

        # Filtre par période (24h, 7j, 30j) en comparant les dates à une date de départ
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

        # Filtre exact sur la catégorie si type_filter est fourni
        if type_filter:
            q = q.where(fn.LOWER(Incident.category) == type_filter.strip().lower())

        # Filtre de recherche simple sur la catégorie
        if search:
            s = search.strip().lower()
            q = q.where(fn.LOWER(Incident.category).contains(s))

        # Transformation des objets Peewee en dictionnaires simples pour l’UI
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


    # Retourne le nombre total d’incidents (KPI global)
    def count_all(self) -> int:
        return Incident.select(fn.COUNT(Incident.id)).scalar() or 0

    # Retourne le nombre d’incidents depuis X jours (KPI temporel)
    def count_since_days(self, days: int) -> int:
        start = datetime.utcnow() - timedelta(days=days)
        return (
            Incident.select(fn.COUNT(Incident.id))
            .where(Incident.date >= start)
            .scalar()
            or 0
        )

    # Retourne les PDQ les plus actifs sur les X derniers jours (classement)
    def top_pdqs(self, *, days: int = 7, limit: int = 8):
        since = datetime.utcnow() - timedelta(days=days)

        q = (
            Incident
            .select(Incident.pdqId, fn.COUNT(Incident.id).alias("count"))
            .where(
                Incident.pdqId.is_null(False),
                Incident.date.is_null(False),
                Incident.date >= since,
            )
            .group_by(Incident.pdqId)
            .order_by(fn.COUNT(Incident.id).desc())
            .limit(limit)
        )

        return [{"pdqId": r.pdqId, "count": int(r.count)} for r in q]

    # Retourne les catégories les plus fréquentes sur les X derniers jours (classement)
    def top_categories(self, *, days: int = 7, limit: int = 10) -> List[Dict]:
        start = datetime.utcnow() - timedelta(days=days)

        q = (
            Incident.select(
                Incident.category.alias("category"),
                fn.COUNT(Incident.id).alias("count"),
            )
            .where((Incident.date >= start) & (Incident.category.is_null(False)))
            .group_by(Incident.category)
            .order_by(fn.COUNT(Incident.id).desc())
            .limit(limit)
        )

        return [{"category": r.category, "count": int(r.count)} for r in q]

    # Supprime un incident selon son identifiant (action admin)
    def delete_incident(self, incident_id: int) -> None:
        Incident.delete().where(Incident.id == incident_id).execute()

    # Compte le nombre de PDQ distincts présents dans tous les incidents (KPI “PDQs”)
    def _count_unique_pdqs_all_time(self) -> int:
        q = (
            Incident.select(Incident.pdqId)
            .where(Incident.pdqId.is_null(False))
            .distinct()
        )
        return q.count()
