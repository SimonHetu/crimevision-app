from peewee import AutoField, CharField, DateTimeField
from ..base_model import BaseModel
import datetime


class User(BaseModel):
    id = AutoField()
    clerkId = CharField(unique=True, column_name="clerkId")
    email = CharField(null=True)
    role = CharField(default="USER")

    createdAt = DateTimeField(
        null=True,
        default=datetime.datetime.utcnow,
        column_name="createdAt",
    )

    updatedAt = DateTimeField(
        null=True,
        default=datetime.datetime.utcnow,
        column_name="updatedAt",
    )

    class Meta:
        table_name = "User"
