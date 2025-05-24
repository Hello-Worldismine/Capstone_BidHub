from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from .models import Property #백엔드 코드
from .models import AutoBidReservation #백엔드 코드
from .models import FavoriteProperty #백엔드 코드


# Removed redundant HTML template rendering functions
# def index(request):
#     return render(request, 'index.html')
# 
# def join(request):
#     return render(request, 'join.html')
# 
# def tender(request):
#     return render(request, 'tender.html')
# 
# def charge(request):
#     return render(request, 'charge.html')
# 
# def auto_bid(request):
#     return render(request, 'auto_bid.html')
# 
# def login(request):
#     return render(request, 'login.html')


# 백엔드 코드 추가
# 자동입찰 예약 API (fetch로 호출하는 POST용)
@csrf_exempt
def auto_bid_reservation(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            case_number = data.get('case_number')
            bid_amount = data.get('bid_amount')
            reserve_time = data.get('reserve_time')
            is_active = data.get('is_active', False)

            # 입력값 검증
            if not case_number or not bid_amount or not reserve_time:
                return JsonResponse({'success': False, 'message': '모든 값을 입력해주세요.'})

            # 예약 정보 저장 (Using the model now)
            AutoBidReservation.objects.create(
                case_number=case_number,
                bid_amount=bid_amount,
                reserve_time=reserve_time,
                is_active=is_active
            )

            return JsonResponse({'success': True, 'message': '예약이 저장되었습니다.'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'JSON 형식 오류'})
    
    return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'})


def search_property(request):
    case_number = request.GET.get('case_number')
    try:
        prop = Property.objects.get(case_number=case_number)
        return JsonResponse({
            'success': True,
            'case_number': prop.case_number,
            'usage': prop.usage
        })
    except Property.DoesNotExist:
        return JsonResponse({'success': False, 'message': '매물을 찾을 수 없습니다.'})
    
# Removed duplicate auto_bid_reservation function

def get_favorite_properties(request):
    favorites = FavoriteProperty.objects.all()
    # Note: This currently gets ALL favorites, not user-specific ones.
    # This should likely be filtered by request.user if authentication is added.
    data = [
        {'case_number': fav.case_number, 'usage': fav.usage}
        for fav in favorites
    ]
    return JsonResponse({'success': True, 'favorites': data})