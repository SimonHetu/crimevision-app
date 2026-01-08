from peewee import AutoField, CharField, DoubleField, IntegerField
from crimevision.core.db.base_model import BaseModel

class Pdq(BaseModel):
    id = AutoField()
    name = CharField()
    address = CharField(null=True)
    cityCode = IntegerField(null=True)
    latitude = DoubleField(null=True)
    longitude = DoubleField(null=True)

    class Meta:
        table_name = "Pdq"
