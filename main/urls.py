from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    # Remove custom login/logout URLs - use allauth instead
    path('tender/', views.tender, name='tender'),
    path('tender/<str:case_number>/', views.tender, name='tender_detail'),
    path('charge/', views.charge, name='charge'),
    path('auto_bid/', views.auto_bid, name='auto_bid'),
    path('mypage/', views.mypage, name='mypage'),
    path('bidform/', views.bidform, name='bidform'),
    path('bidform/submit/', views.bid_submit, name='bid_submit'),
    path('detail/<str:case_number>/', views.property_detail, name='property_detail'),
    path('api/favorites/', views.get_favorite_properties, name='get_favorites'), #즐겨찾기
    # Add new URL patterns for referenced views
    path('bid_history/', views.bid_history, name='bid_history'),
    path('refund/', views.refund, name='refund'),
    path('favorites/', views.favorites, name='favorites'),
    path('update_wallet/', views.update_wallet, name='update_wallet'),
]

