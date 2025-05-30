from django.urls import path
from . import views

urlpatterns = [
    # Removed redundant template rendering URLs
    # path('', views.index, name='index'),
    # path('login/', views.login, name='login'),
    # path('join/', views.join, name='join'),
    # path('tender/', views.tender, name='tender'),
    # path('charge/', views.charge, name='charge'),
    # path('auto_bid/', views.auto_bid, name='auto_bid'),
    path('api/auto-bid/', views.auto_bid_reservation, name='auto_bid_reservation'),
    path('api/search-property/', views.search_property, name='search_property'),
    path('api/favorites/', views.get_favorite_properties, name='get_favorites'), #즐겨찾기
]

