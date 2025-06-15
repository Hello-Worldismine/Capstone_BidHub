from django.db import models
from django.conf import settings

class Property(models.Model):
    """매물 정보 모델"""
    case_number = models.CharField(max_length=50, unique=True, verbose_name="사건번호")
    usage = models.CharField(max_length=100, verbose_name="용도")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.case_number} - {self.usage}"
    
    class Meta:
        verbose_name = "매물"
        verbose_name_plural = "매물들"

class AutoBidReservation(models.Model):
    """자동입찰 예약 모델"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="사용자"
    )
    case_number = models.CharField(max_length=50, verbose_name="사건번호")
    bid_amount = models.DecimalField(max_digits=15, decimal_places=0, verbose_name="입찰금액")
    reserve_time = models.DateTimeField(verbose_name="예약시간")
    is_active = models.BooleanField(default=True, verbose_name="활성화 여부")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.case_number} - {self.bid_amount}원"
    
    class Meta:
        verbose_name = "자동입찰 예약"
        verbose_name_plural = "자동입찰 예약들"

class AutoBidFavorite(models.Model):  # 이름 변경
    """자동입찰용 즐겨찾기 매물 모델"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        verbose_name="사용자"
    )
    case_number = models.CharField(max_length=50, verbose_name="사건번호")
    usage = models.CharField(max_length=100, verbose_name="용도")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.case_number} - {self.usage}"
    
    class Meta:
        verbose_name = "자동입찰 즐겨찾기"
        verbose_name_plural = "자동입찰 즐겨찾기들"
        unique_together = ['user', 'case_number']
