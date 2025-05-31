from django.urls import path
from . import views

urlpatterns = [
    # 기존 페이지들
    path('', views.index, name='index'),
    path('tender/', views.tender, name='tender'),
    path('tender/<str:case_number>/', views.tender, name='tender_detail'),
    path('auto_bid/', views.auto_bid, name='auto_bid'),
    path('mypage/', views.mypage, name='mypage'),
    path('bidform/', views.bidform, name='bidform'),
    path('bid_submit/', views.bid_submit, name='bid_submit'),
    path('charge/', views.charge, name='charge'),
    path('property/<str:case_number>/', views.property_detail, name='property_detail'),
    path('bid_history/', views.bid_history, name='bid_history'),
    path('refund/', views.refund, name='refund'),
    path('favorites/', views.favorites, name='favorites'),
    path('update_wallet/', views.update_wallet, name='update_wallet'),
    
    # 빠른 검색 페이지
    path('fsearch/', views.fsearch, name='fsearch'),
    # 조건검색 페이지 (AJAX와 일반 요청 모두 처리)
    path('csearch/', views.csearch, name='csearch'),
    
    # API 엔드포인트들
    path('api/get-favorite-properties/', views.get_favorite_properties, name='get_favorite_properties'),
    path('api/search-cases/', views.search_cases_api, name='search_cases_api'),
]

