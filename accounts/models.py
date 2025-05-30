from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    # 성별, 생년월일, 자기소개
    gender = models.CharField(max_length=1, choices=[('M', 'Male'), ('F', 'Female')], blank=True)
    birth_date = models.DateField(null=True, blank=True)
    bio = models.TextField(blank=True)

    # 추가 필드
    region = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    mobile = models.CharField(max_length=20, blank=True)
    terms_conditions = models.BooleanField(default=False)  # 이용약관 동의

    class Meta:
        db_table = 'custom_user'
