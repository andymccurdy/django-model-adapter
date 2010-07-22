from django.db import models
from django.contrib.auth.models import User
from model_adapter import AdaptiveForeignKey

class FKAdaptedViaString(models.Model):
    user = AdaptiveForeignKey(User)

class FKAdaptedViaDict(models.Model):
    user = AdaptiveForeignKey(User)

class FKAdaptedViaDictWithMap(models.Model):
    user = AdaptiveForeignKey(User)

class FKNotAdapted(models.Model):
    user = AdaptiveForeignKey(User)
