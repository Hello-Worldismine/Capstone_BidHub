from django.urls import path, include
from . import views
from app.views import load_bid_history

urlpatterns = [
    # 기존 페이지들
    path('', views.index, name='index'),
    path('tender/', views.tender, name='tender'),
    path('tender/<str:case_number>/', views.tender, name='tender_detail'),
    path('auto_bid/', views.auto_bid, name='auto_bid'),
    path('mypage/', views.mypage, name='mypage'),
    path('join/', views.join, name='join'),
    path('login/', views.login, name='login'),
    path('bidform/', views.bidform, name='bidform'),
    path('bid_submit/', views.bid_submit, name='bid_submit'),
    path('charge/', views.charge, name='charge'),
    path('property/<str:case_number>/', views.property_detail, name='property_detail'),
    path('bid_history/', views.bid_history, name='bid_history'),
    path('favlist/', views.favlist, name='favlist'),
    path('update_wallet/', views.update_wallet, name='update_wallet'),
    path('chat/', views.chat_view, name='chatbot'),
    
    # 빠른 검색 페이지
    path('fsearch/', views.fsearch, name='fsearch'),

    # 조건 검색 페이지
    path('csearch/', views.csearch, name='csearch'),
    
    # API 엔드포인트들
    path('api/get-favorite-properties/', views.get_favorite_properties, name='get_favorite_properties'),
    path('api/search-cases/', views.search_cases_api, name='search_cases_api'),

    #아이디 찾기
    path('find-id/', views.find_id, name='find_id'),

    #오늘의 경매, 주간경매공고 페이지
    path('today-bid/', views.today_bid, name='today_bid'),
    path('week-bid/', views.week_bid, name='week_bid'),
    
    #입찰
    path("api/", include("app.urls"))
]

