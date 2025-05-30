from django.contrib import admin
from .models import Property, AutoBidReservation  
from .models import FavoriteProperty

admin.site.register(Property) # 임시db
admin.site.register(AutoBidReservation) # 예약 목록
admin.site.register(FavoriteProperty) # 임시 즐겨찾기 목록