from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_view, name='login'),  # 함수명 변경에 맞춤
    path('join/', views.join, name='join'),
    path('tender/', views.tender, name='tender'),
    path('charge/', views.charge, name='charge'),
    path('auto_bid/', views.auto_bid, name='auto_bid'),
    path('mypage/', views.mypage, name='mypage'),
    path('bidform/', views.bidform, name='bidform'),
    path('bidform/submit/', views.bid_submit, name='bid_submit'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('fsearch/', views.fsearch, name='fsearch'),
    path('csearch/', views.csearch, name='csearch'),
    path('bid_history/', views.bid_history, name='bid_history'),
    path('favlist/', views.favlist, name='favlist'),

    path('register/', views.register, name='register'), # 추가
]

