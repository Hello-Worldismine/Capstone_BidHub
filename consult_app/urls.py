from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='consult_app'),  # 상담 시작 → 법원 선택 화면
    path('enter/', views.enter_court_room, name='enter_court_room'),  # 법원 선택 후 이동

    path('agent/dashboard/', views.agent_dashboard, name='agent_dashboard'),
    path('agent/dashboard/rooms/', views.active_rooms_api, name='active_rooms_api'),
    path('agent/complete/<str:room_name>/', views.complete_chat, name='complete_chat'),
    path('agent/<str:room_name>/', views.agent_room, name='agent_room'),

    path('<str:room_name>/', views.room, name='room'),  # 사용자 채팅방
]
