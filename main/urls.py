from django.urls import path
from . import views
# import django.contrib.auth.views # Removed import

urlpatterns = [
    path('', views.index, name='index'),
    # path('login/', views.login, name='login'), # Removed
    # path('join/', views.join, name='join'), # Removed
    path('tender/', views.tender, name='tender'),
    path('charge/', views.charge, name='charge'),
    path('auto_bid/', views.auto_bid, name='auto_bid'),
    path('mypage/', views.mypage, name='mypage'),
    path('bidform/', views.bidform, name='bidform'),
    path('bidform/submit/', views.bid_submit, name='bid_submit'),
    path('detail/<str:case_number>/', views.property_detail, name='property_detail'),
    path('api/favorites/', views.get_favorite_properties, name='get_favorites'), #즐겨찾기
    # path('logout/', django.contrib.auth.views.LogoutView.as_view(), name='logout'), # Removed
]

