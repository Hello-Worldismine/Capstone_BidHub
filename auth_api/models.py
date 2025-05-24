from django.db import models

class Property(models.Model):
    case_number = models.CharField(max_length=100, unique=True)  # 예: 2024타경118895
    usage = models.CharField(max_length=100)  # 예: 다세대주택

    def __str__(self):
        return f"{self.case_number} - {self.usage}"


class AutoBidReservation(models.Model):
    case_number = models.CharField(max_length=50)
    bid_amount = models.PositiveIntegerField()
    reserve_time = models.TimeField()
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.case_number} - {self.bid_amount}원 at {self.reserve_time}"
    
class FavoriteProperty(models.Model):
    case_number = models.CharField(max_length=50)
    usage = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.case_number} / {self.usage}"