from django.urls import path, include
from . import views
from app.views import load_bid_history

urlpatterns = [
    # 기존 페이지들
    path('', views.index, name='index'),
    path('tender/', views.tender, name='tender'),
    path('tender/<str:case_number>/', views.tender, name='tender_detail'),
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
    path("api/", include("app.urls")),

    #매각결과조회
    path('result/', views.result, name='result'),
    path('region_result/', views.region_result, name='region_result'),

    
path('consult_app/', views.consult_index, name='consult_app'),  # /consult_app/
path('consult_app/enter/', views.consult_enter_court_room, name='enter_court_room'),
path('consult_app/agent/dashboard/', views.consult_agent_dashboard, name='agent_dashboard'),
path('consult_app/agent/dashboard/rooms/', views.consult_active_rooms_api),
path('consult_app/agent/complete/<str:room_name>/', views.consult_complete_chat, name='complete_chat'),
path('consult_app/agent/<str:room_name>/', views.consult_agent_room, name='agent_room'),
path('consult_app/<str:room_name>/', views.consult_user_room, name='user_room'),


    # 프로필 관련 URL
    path('update_profile/', views.update_profile, name='update_profile'),
]



