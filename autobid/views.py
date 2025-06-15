# autobid/views.py
import json
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model  # User 모델을 동적으로 가져오기
from django.utils.safestring import mark_safe  # 🔸 이 줄 추가!
from main.models import FavoriteProperty
from app.models import AuctionItem
from .models import Property, AutoBidReservation, AutoBidFavorite  # 모델명 변경

User = get_user_model()  # 현재 설정된 User 모델 가져오기

@login_required
def auto_bid(request):
    """자동입찰 페이지 - 컴포넌트 사용"""
    
    # 기존 favlist와 동일한 데이터 가져오기
    user_favorites = FavoriteProperty.objects.filter(user=request.user)
    favorite_items = []
    
    for fav in user_favorites:
        try:
            # 사건번호로 AuctionItem 찾기
            auction_items = AuctionItem.objects.filter(
                case_number__case_number=fav.case_number
            ).select_related('case_number')
            
            for item in auction_items:
                item.is_favorite = True  # 이미 즐겨찾기 상태
                favorite_items.append(item)
                
        except AuctionItem.DoesNotExist:
            continue
    
    # JavaScript용 JSON 데이터도 준비
    favorites_data = []
    for item in favorite_items:
        favorites_data.append({
            'case_number': item.case_number.case_number,
            'property_type': item.property_type or '매물 정보',
            'property_address': item.property_address or '주소 정보 없음',
        })
    
    return render(request, 'autobid/auto_bid.html', {
        'favorite_items': favorite_items,  # 컴포넌트용
        'favorites_data_json': mark_safe(json.dumps(favorites_data)),  # JavaScript용
    })

@csrf_exempt
def auto_bid_reservation(request):
    """자동입찰 예약 처리 API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)

            case_number = data.get('case_number')
            bid_amount = data.get('bid_amount')
            reserve_time = data.get('reserve_time')
            is_active = data.get('is_active', False)

            if not case_number or not bid_amount or not reserve_time:
                return JsonResponse({'success': False, 'message': '모든 값을 입력해주세요.'})

            reservation = AutoBidReservation.objects.create(
                user=request.user if request.user.is_authenticated else None,
                case_number=case_number,
                bid_amount=bid_amount,
                reserve_time=reserve_time,
                is_active=is_active
            )

            return JsonResponse({'success': True, 'message': '예약이 저장되었습니다.'})

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'JSON 형식 오류'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'})

def search_property(request):
    """매물 검색 API"""
    case_number = request.GET.get('case_number')
    
    if not case_number:
        return JsonResponse({'success': False, 'message': '사건번호를 입력해주세요.'})
    
    try:
        from app.models import AuctionCase, AuctionItem
        
        try:
            case = AuctionCase.objects.get(case_number=case_number)
            item = AuctionItem.objects.filter(case_number=case).first()
            
            usage = "정보 없음"
            if item and item.property_name:
                usage = item.property_name
            elif case.case_name:
                usage = case.case_name
                
            return JsonResponse({
                'success': True,
                'case_number': case.case_number,
                'usage': usage
            })
        except AuctionCase.DoesNotExist:
            pass
        
        prop = Property.objects.get(case_number=case_number)
        return JsonResponse({
            'success': True,
            'case_number': prop.case_number,
            'usage': prop.usage
        })
        
    except Property.DoesNotExist:
        return JsonResponse({'success': False, 'message': '매물을 찾을 수 없습니다.'})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'검색 중 오류가 발생했습니다: {str(e)}'})

def get_favorite_properties(request):
    """즐겨찾기 매물 조회 API"""
    try:
        if request.user.is_authenticated:
            favorites = AutoBidFavorite.objects.filter(user=request.user)  # 변경
        else:
            favorites = AutoBidFavorite.objects.all()  # 변경
            
        data = [
            {
                'case_number': fav.case_number, 
                'usage': fav.usage,
                'created_at': fav.created_at.strftime('%Y-%m-%d %H:%M')
            }
            for fav in favorites
        ]
        return JsonResponse({'success': True, 'favorites': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'조회 중 오류가 발생했습니다: {str(e)}'})

@csrf_exempt
def add_favorite_property(request):
    """즐겨찾기 추가 API"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            case_number = data.get('case_number')
            usage = data.get('usage', '정보 없음')
            
            if not case_number:
                return JsonResponse({'success': False, 'message': '사건번호를 입력해주세요.'})
            
            if request.user.is_authenticated:
                existing = AutoBidFavorite.objects.filter(  # 변경
                    user=request.user, 
                    case_number=case_number
                ).first()
            else:
                existing = AutoBidFavorite.objects.filter(  # 변경
                    case_number=case_number
                ).first()
            
            if existing:
                return JsonResponse({'success': False, 'message': '이미 즐겨찾기에 있는 매물입니다.'})
            
            AutoBidFavorite.objects.create(  # 변경
                user=request.user if request.user.is_authenticated else None,
                case_number=case_number,
                usage=usage
            )
            
            return JsonResponse({'success': True, 'message': '즐겨찾기에 추가되었습니다.'})
            
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'JSON 형식 오류'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': 'POST 요청만 허용됩니다.'})
