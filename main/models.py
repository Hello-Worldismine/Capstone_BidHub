from django.db import models

# Create your models here.
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wallet_address = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100, blank=True)
    id_number = models.CharField(max_length=20, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=200, blank=True)
    balance = models.PositiveIntegerField(default=0)  # 예치금 (원 단위)

    def __str__(self):
        return f"{self.user.username}의 프로필"
