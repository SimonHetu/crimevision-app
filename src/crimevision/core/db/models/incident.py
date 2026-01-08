from peewee import AutoField, CharField, DateTimeField, DoubleField, IntegerField
from crimevision.core.db.base_model import BaseModel

class Incident(BaseModel):
    id = AutoField()
    category = CharField(null=True)
    date = DateTimeField(null=True)
    timePeriod = CharField(null=True)
    x = DoubleField(null=True)
    y = DoubleField(null=True)
    longitude = DoubleField(null=True)
    latitude = DoubleField(null=True)
    pdqId = IntegerField(null=True)
    source = CharField(null=True)
    sourceId = IntegerField(null=True)

    class Meta:
        table_name = "Incident"
