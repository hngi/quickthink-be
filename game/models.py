import uuid

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models


# Create your models here.
def add_one():
    largest = Game.objects.all().order_by('game_code').last()
    if not largest:
        return 1000
    return largest.game_code + 1


class Category(models.Model):
    name = models.CharField(primary_key=True, max_length=100, unique=True, null=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True,editable=False)


class Game(models.Model):
    game_code = models.IntegerField(primary_key=True,editable=False,
                                    default=add_one)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    user_name = models.CharField(max_length=100, null=False)
    active = models.BooleanField(default=True)


class Options(models.Model):
    option = models.CharField(primary_key=True, max_length=100000, unique=True, null=False)


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    question = models.CharField(max_length=100000, unique=False, null=False)
    options = models.ManyToManyField("Options")
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    answer = models.ForeignKey(Options, related_name="correct", on_delete=models.PROTECT)


class UserGames(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game_code = models.ForeignKey(Game,
                                  on_delete=models.PROTECT)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    user_name = models.CharField(max_length=100, null=False)
    score = models.PositiveIntegerField(
        null=False, validators=[MinValueValidator(1)], default=0
    )


