from fastapp.models import Model, fields, BaseMeta

class Tournament(Model):
    # Defining `id` field is optional, it will be defined automatically
    # if you haven't done it yourself
    name = fields.CharField(max_length=255)

    def __str__(self):
        return self.name




class Team(Model):
    name = fields.CharField(max_length=255)


    def __str__(self):
        return self.name


class Event(Model):
    name = fields.CharField(max_length=255)
    tournament = fields.ForeignKeyField(Tournament, related_name='events')
    participants = fields.ManyToManyField(Team, related_name='events', through='event_team')

    def __str__(self):
        return self.name


class ExternalData(Model):
    name = fields.CharField(max_length=255)


    def __str__(self):
        return self.name
    
    class Meta(BaseMeta):
        external = True