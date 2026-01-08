from peewee import AutoField, CharField, DateTimeField
from ..base_model import BaseModel
import datetime

class User(BaseModel):
    id = AutoField()
    email = CharField(unique=True)
    name = CharField()
    pseudo = CharField()
    createdAt = DateTimeField(null=True)
    updatedAt = DateTimeField(null=True)
    hashedPassword = CharField()

    class Meta:
        table_name = "User"
