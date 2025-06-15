# autobid/urls.py
from django.urls import path
from . import views


urlpatterns = [
    path('', views.auto_bid, name='auto_bid'),
    path('api/reservation/', views.auto_bid_reservation, name='reservation'),
    path('api/search-property/', views.search_property, name='search_property'),
    path('api/favorites/', views.get_favorite_properties, name='get_favorites_api'),
    path('api/add-favorite/', views.add_favorite_property, name='add_favorite'),
]