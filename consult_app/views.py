import uuid
from django.shortcuts import redirect, render
from .active_rooms import active_rooms, room_assignments
from django.http import JsonResponse

# 실시간 방 목록 API
# 실시간 방 목록 API
def consult_active_rooms_api(request):
    return JsonResponse({'rooms': list(active_rooms)})

def active_rooms_api(request):
    return JsonResponse({'rooms': list(active_rooms)})

# 사용자 채팅방 입장
def room(request, room_name):
    if room_name not in active_rooms:
        active_rooms.append(room_name)  # 중복 방지 + 순서 보장
    return render(request, 'consult_app/room.html', {
        'room_name': room_name,
        'is_agent': False
    })

# 상담원 채팅방 입장
def agent_room(request, room_name):
    if room_name in room_assignments:
        return render(request, 'consult_app/already_assigned.html', {
            'room_name': room_name,
            'assigned_to': room_assignments[room_name]
        })
    room_assignments[room_name] = "상담원1"
    return render(request, 'consult_app/room.html', {
        'room_name': room_name,
        'is_agent': True
    })

# 사용자가 진입하는 기본화면: 법원 선택 화면
def index(request):
    court_list = [
    "서울고등법원", "서울중앙지방법원", "서울동부지방법원", "서울서부지방법원", "서울북부지방법원",
    "서울남부지방법원", "서울가정법원", "서울행정법원", "서울회생법원",
    "의정부지방법원", "고양지원", "남양주지원", "수원지방법원",
    "성남지원", "여주지원", "평택지원", "안산지원", "안양지원"
]
    return render(request, 'consult_app/select_court.html', {
        'court_list': court_list
    })

# 법원 선택 후 채팅방으로 이동
def enter_court_room(request):
    selected_court = request.POST.get('court')
    if selected_court in COURT_CODE_MAP:
        base = COURT_CODE_MAP[selected_court]
        suffix = str(uuid.uuid4())[:8]  # 사용자별 고유 방
        room_id = f"{base}-{suffix}"
        return redirect(f'/consult_app/{room_id}/')
    return redirect('/consult_app/')

# 상담원 대시보드
def agent_dashboard(request):
    return render(request, 'consult_app/agent_dashboard.html', {
        'active_rooms': active_rooms
    })

# 상담 종료 처리
def complete_chat(request, room_name):
    if room_name in active_rooms:
        active_rooms.remove(room_name)
        return JsonResponse({'status': 'success', 'message': '방 제거됨'})
    else:
        return JsonResponse({'status': 'error', 'message': '해당 방 없음'})


COURT_CODE_MAP = {
    "서울고등법원": "seoul_high",
    "서울중앙지방법원": "seoul_1",
    "서울동부지방법원": "seoul_2",
    "서울서부지방법원": "seoul_3",
    "서울북부지방법원": "seoul_4",
    "서울남부지방법원": "seoul_5",
    "서울가정법원": "seoul_family",
    "서울행정법원": "seoul_admin",
    "의정부지방법원": "uijeongbu",
    "수원지방법원": "suwon_1",
    "서울회생법원": "seoul_rehab",
    "수원고등법원": "suwon_high",
    "수원가정법원": "suwon_family",
    "수원회생법원": "suwon_rehab"
}
