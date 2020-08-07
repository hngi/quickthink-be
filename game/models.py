import uuid

from django.contrib.auth.models import User
from django.core.validators import MinValueValidator
from django.db import models
from datetime import datetime

# Create your models here.
def add_one():
    largest = Game.objects.all().order_by("game_code").last()
    if not largest:
        return 1000
    return largest.game_code + 1


class Category(models.Model):
    name = models.CharField(primary_key=True, max_length=100, unique=True, null=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    isGeneral = models.BooleanField(default=False)
    isSubCategory = models.BooleanField(default=False, null=True)
    parentCategory = models.ForeignKey('self', on_delete=models.PROTECT, null=True)


class Game(models.Model):
    game_code = models.IntegerField(primary_key=True, editable=False, default=add_one)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    user_name = models.CharField(max_length=100, null=False)
    active = models.BooleanField(default=True)


class Options(models.Model):
    option = models.CharField(
        primary_key=True, max_length=100000, unique=True, null=False
    )


DIFFICULTY_CHOICES = (
    ("easy", "easy"),
    ("difficult", "difficult"),
    ("medium", "medium")
)


class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    question = models.CharField(max_length=100000, unique=False, null=False)
    options = models.ManyToManyField("Options")
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    difficulty = models.CharField(
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='easy'
    )
    answer = models.ForeignKey(
        Options, related_name="correct", on_delete=models.PROTECT
    )


class UserGames(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game_code = models.ForeignKey(Game,
                                  on_delete=models.CASCADE, null=True)
    category = models.ManyToManyField(Category)
    user_name = models.CharField(max_length=100, null=True)
    email_address = models.CharField(max_length=100, null=True)
    score = models.PositiveIntegerField(
        null=False, validators=[MinValueValidator(1)], default=0
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    time = models.CharField(max_length=100, null=True)  # inseconds


class Newsletter(models.Model):
    email = models.EmailField(null=False, unique=True, blank=False)
    created_at = models.DateTimeField(default=datetime.now, blank=True)


class ContactUs(models.Model):
    email = models.EmailField(null=False, blank=False, unique=False)
    full_name = models.CharField(max_length=100, null=False, blank=False)
    message = models.TextField(null=False)
    created_at = models.DateTimeField(default=datetime.now, blank=True)


class UserStreaks(models.Model):
    email_address = models.CharField(max_length=100, null=False, unique=True, primary_key=True)
    streaks = models.PositiveIntegerField(
        null=False, validators=[MinValueValidator(0)], default=0
    )
    score = models.PositiveIntegerField(
        null=False, validators=[MinValueValidator(0)], default=0
    )
    last_played = models.DateField(null=True)
