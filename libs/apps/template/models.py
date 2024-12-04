from libs import models
from tortoise import fields


class Tournament(models.Model):
    name = models.CharField(max_length=255)

    events: fields.ReverseRelation["Event"]

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=255)

    events: fields.ReverseRelation["Event"]

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=255)
    tournament: models.ForeignKeyRelation["Tournament"] = models.ForeignKeyField(
        Tournament, related_name="events"
    )
    participants = models.ManyToManyField(
        Team, related_name="events", through="event_team"
    )

    def __str__(self):
        return self.name
