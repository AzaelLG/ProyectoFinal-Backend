from django.db import models


class User(models.Model):
    username = models.CharField(max_length = 100,unique=True)
    password = models.CharField(max_length = 200)
    session_token = models.CharField(max_length=200, unique=True, null=True, blank=True)
    volume = models.IntegerField(default=50)
    resolution_choices = [
        (1, 'Fullscreen'),
        (2, 'Windowed')
    ]
    resolution = models.IntegerField(choices=resolution_choices, default=1)

class Character(models.Model):
    name = models.CharField(max_length = 100,unique=True)
    price = models.IntegerField(default=0)
    base_life = models.IntegerField(default=0)
    base_dmg = models.FloatField(default=0)
    base_defense = models.FloatField(default=0)
    base_luck = models.FloatField(default=0)
    exp_multiplier = models.FloatField(default=0)
    base_movspeed = models.FloatField(default=0)
    base_atckspeed = models.FloatField(default=0)

class Run(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    time = models.IntegerField(default=0)
    lvl_max = models.IntegerField(default=0)
    datetime = models.DateTimeField(auto_now=True)

class UserCharacterSelected(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    character = models.ForeignKey(Character, on_delete=models.CASCADE)
    is_selected = models.BooleanField(default=False)