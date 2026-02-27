from typing import List, Dict, Optional
from peewee import fn
from crimevision.core.db.models.pdq import Pdq
from crimevision.core.db.database import get_db

class PdqService:
    def list_pdqs(self, limit: int = 200, search: str = "") -> List[Dict]:
        q = Pdq.select().order_by(Pdq.id).limit(limit)
        if search:
            s = search.strip()
            if s.isdigit():
                q = q.where(Pdq.id == int(s))
            else:
                q = q.where(fn.LOWER(Pdq.name).contains(s.lower()))
        return [
            {
                "id": p.id,
                "name": p.name,
                "address": p.address,
                "cityCode": p.cityCode,
                "latitude": p.latitude,
                "longitude": p.longitude,
            }
            for p in q
        ]
    
    def get_pdq_by_id(self, pdq_id: int) -> Optional[Dict]:
        p = Pdq.get_or_none(Pdq.id == pdq_id)
        if not p:
            return None
        return {
            "id": p.id,
            "name": p.name,
            "address": p.address,
            "cityCode": p.cityCode,
            "latitude": p.latitude,
            "longitude": p.longitude,
        }
    
