from typing import List, Dict, Optional

from datetime import datetime, timedelta
from peewee import fn

from crimevision.core.db.models.incident import Incident


class IncidentService:
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

        if pdq_id is not None:
            q = q.where(Incident.pdqId == pdq_id)

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

        if type_filter:
            q = q.where(fn.LOWER(Incident.category) == type_filter.strip().lower())

        if search:
            s = search.strip().lower()
            q = q.where(fn.LOWER(Incident.category).contains(s))

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

    def count_all(self) -> int:
        return Incident.select(fn.COUNT(Incident.id)).scalar() or 0

    def count_since_days(self, days: int) -> int:
        start = datetime.utcnow() - timedelta(days=days)
        return (
            Incident.select(fn.COUNT(Incident.id))
            .where(Incident.date >= start)
            .scalar()
            or 0
        )

    def top_pdqs(self, *, days: int = 7, limit: int = 8):
        since = datetime.utcnow() - timedelta(days=days)

        q = (
            Incident.select(Incident.pdqId, fn.COUNT(Incident.id).alias("count"))
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

    def delete_incident(self, incident_id: int) -> None:
        Incident.delete().where(Incident.id == incident_id).execute()

    def _count_unique_pdqs_all_time(self) -> int:
        q = (
            Incident.select(Incident.pdqId)
            .where(Incident.pdqId.is_null(False))
            .distinct()
        )
        return q.count()

    # -------------------------
    # NEW: used by StatsPage / Detail dialog
    # -------------------------
    def count_unique_pdqs(self) -> int:
        q = (
            Incident.select(Incident.pdqId)
            .where(Incident.pdqId.is_null(False))
            .distinct()
        )
        return q.count()

    def get_incident_by_id(self, incident_id: int) -> Optional[Dict]:
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
    def top_categories(self, *, days: int = 30, limit: int = 10) -> List[Dict]:
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

    def top_pdqs(self, *, days: int = 30, limit: int = 10) -> List[Dict]:
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

    def count_by_day(self, *, days: int = 30) -> List[Dict]:
        """
        Returns [{"day": "YYYY-MM-DD", "count": N}, ...] for last X days.
        Uses SQL date truncation to group by day.
        """
        start = datetime.utcnow() - timedelta(days=days)

        # Postgres: DATE_TRUNC('day', date)
        day_expr = fn.DATE_TRUNC("day", Incident.date).alias("day")

        q = (
            Incident.select(
                day_expr,
                fn.COUNT(Incident.id).alias("count"),
            )
            .where(
                Incident.date.is_null(False),
                Incident.date >= start,
            )
            .group_by(day_expr)
            .order_by(day_expr)
        )

        out: List[Dict] = []
        for r in q:
            # r.day est souvent un datetime "00:00"
            d = r.day
            day_str = d.strftime("%Y-%m-%d") if hasattr(d, "strftime") else str(d)
            out.append({"day": day_str, "count": int(r.count)})
        return out