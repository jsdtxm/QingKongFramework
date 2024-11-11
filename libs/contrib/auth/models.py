from libs import models


class AbstractUser(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)

    email = models.EmailField(blank=True)

    is_active = models.BooleanField(default=True)

    class Meta:
        abstract = True


class User(models.Model):
    pass
