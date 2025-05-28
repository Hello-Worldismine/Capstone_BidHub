# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Profile
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal # Import Decimal
from django.templatetags.static import static # Import static function
from django.conf import settings # Import settings
from app.models import AuctionItem, AuctionCase, ClaimDistribution, PropertyListing, AuctionParty
from django.utils import timezone # Add timezone import

def index(request):
    # Fetch auction items
    # You might want to add filtering here, e.g., by date or status
    # For example: auction_items = AuctionItem.objects.filter(auction_date__gte=timezone.now()).order_by('auction_date')
    auction_items = AuctionItem.objects.select_related('case_number').all()[:10]
    context = {
        'auction_items': auction_items  # 이제 property_name도 포함됨
    }
    return render(request, 'main/pages/index.html', context) # Pass context to the template

def get_status_text(status_code):
    """상태 코드를 텍스트로 변환"""
    status_mapping = {
        '001': '매각',
        '002': '유찰', 
        '003': '매각허가',
        '004': '매각불허가',
        '005': '최고가매각불허가결정',
        '006': '중지',
        '007': '진행중',
        '008': '예정',
        '009': '취하',
        '010': '미납',
        '011': '철회',
        '012': '연기'
    }
    return status_mapping.get(status_code, '진행중')

def tender(request, case_number=None):
    if case_number:
        try:
            case = get_object_or_404(AuctionCase, case_number=case_number)
            item_details = AuctionItem.objects.filter(case_number=case).first()
            
            if not item_details:
                return redirect('index')
            
            # Get related data for display
            claim_distribution = ClaimDistribution.objects.filter(case_number=case).first()
            property_listings = PropertyListing.objects.filter(case_number=case)
            interested_parties = AuctionParty.objects.filter(case_number=case)
            
            # 감정평가액 (기준 가격)
            valuation_amount = 0
            if item_details and item_details.valuation_amount:
                valuation_amount = int(item_details.valuation_amount.replace(',', '')) if isinstance(item_details.valuation_amount, str) else item_details.valuation_amount
            
            # AuctionSchedule에서 현재 진행중인 매각기일 찾기
            from app.models import AuctionSchedule
            from django.utils import timezone
            
            schedules = AuctionSchedule.objects.filter(auction_item=item_details).order_by('round_number')
            
            # 현재 진행중인 매각기일의 최저매각가격 찾기
            current_min_price = valuation_amount  # 기본값
            current_round = 1
            
            now = timezone.now().date()
            
            for schedule in schedules:
                # 매각기일이고 아직 지나지 않은 경우
                if (schedule.schedule_type == '매각기일' and 
                    schedule.auction_date and 
                    schedule.auction_date.date() >= now and
                    schedule.minimum_price and 
                    schedule.minimum_price > 0):
                    
                    current_min_price = schedule.minimum_price  # tsLwsDspslPrc 값 사용
                    current_round = schedule.round_number
                    break
                
                # 과거 매각기일 중 가장 최근 회차 확인 (다음 회차 예측용)
                elif (schedule.schedule_type == '매각기일' and 
                      schedule.auction_date and 
                      schedule.auction_date.date() < now):
                    current_round = schedule.round_number + 1  # 다음 회차
            
            # 만약 진행중인 매각기일을 찾지 못했다면 감정평가액 사용
            if current_min_price == valuation_amount and schedules.exists():
                # 가장 최근 스케줄의 minimum_price 사용
                latest_schedule = schedules.filter(
                    schedule_type='매각기일',
                    minimum_price__gt=0
                ).first()
                
                if latest_schedule:
                    current_min_price = latest_schedule.minimum_price
                    current_round = latest_schedule.round_number
            
            # 감정평가액 대비 비율 계산
            price_ratio = 100
            if valuation_amount > 0:
                price_ratio = round((current_min_price / valuation_amount) * 100)
            
            property_info = {
                'case_number': case.case_number if case else None,
                'case_name': case.case_name if case else None,
                'property_name': item_details.property_name if item_details else None,
                'court': case.court_name if case else None,
                'receipt_date': case.filing_date if case else None,
                'responsible_dept': case.responsible_dept if case else None,
                'claim_amount': case.claim_amount if case else None,
                'appeal_status_display': '항고' if case and case.appeal_status else '미항고',
                'min_bid_price': f"{current_min_price:,}",  # 실제 tsLwsDspslPrc 값
                'current_round': current_round,
                'valuation_amount': f"{valuation_amount:,}",
                'price_ratio': price_ratio,  # 감정가 대비 비율
                'specification_url': item_details.item_spec_url if item_details else None
            }
            
            location_info = {
                'location': claim_distribution.location if claim_distribution else None,
                'claim_deadline': claim_distribution.claim_deadline if claim_distribution else None,
                'case_number': case.case_number if case else None
            }
            
            document_urls = {
                'specification_url': item_details.item_spec_url if item_details else None
            }
            
            # 입찰 내역 현황 - AuctionSchedule 모델 사용
            bidding_history = []
            
            if item_details and item_details.valuation_amount:
                try:
                    val_amount_str = item_details.valuation_amount or "0"
                    val_amount_str = ''.join(c for c in val_amount_str if c.isdigit() or c == '.')
                    valuation_amount = float(val_amount_str)
                except (ValueError, TypeError):
                    valuation_amount = 0
                
            # AuctionSchedule에서 회차별 정보 가져오기
            if item_details:
                from app.models import AuctionSchedule
                schedules = AuctionSchedule.objects.filter(auction_item=item_details).order_by('round_number')
                
                for schedule in schedules:
                    # 실제 저장된 minimum_price 사용 (tsLwsDspslPrc 값)
                    min_price = schedule.minimum_price if schedule.minimum_price else 0
                    
                    # 보증금 계산 (최저매각가격의 10%)
                    deposit_amount = int(min_price * 0.1) if min_price > 0 else 0
                    
                    # 상태 결정
                    status = get_status_text(schedule.result_status)
                    
                    # 기일 종류에 따른 표시 텍스트
                    schedule_display = schedule.schedule_type or f"{schedule.round_number}차"
                    
                    bidding_history.append({
                        'id': schedule.round_number,
                        'link_text': f"{case.case_number} {schedule_display}",
                        'type': schedule_display,  # "매각기일", "매각결정기일" 등
                        'min_price': f"{min_price:,}" if min_price > 0 else "정보없음",
                        'status': status,
                        'auction_date': schedule.auction_date,
                        'due_date': schedule.decision_date
                    })
            
            # 이미지 경로 준비
            image_paths = []
            if item_details and item_details.item_image_url:
                for url in item_details.item_image_url.split(','):
                    if url.strip():
                        image_paths.append(url.strip())
            
            context = {
                'property_id': case_number,
                'property_info': property_info,
                'item_details': item_details,
                'case': case,
                'location_info': location_info,
                'document_urls': document_urls,
                'bidding_history': bidding_history,
                'building_details': property_listings,
                'interested_parties': interested_parties,
                'image_paths': image_paths,
                'naver_maps_client_id': getattr(settings, 'NAVER_MAPS_CLIENT_ID', '')
            }
            
            return render(request, 'main/pages/tender.html', context)
            
        except (AuctionCase.DoesNotExist, AuctionItem.DoesNotExist):
            return redirect('index')
    else:
        return render(request, 'main/pages/tender.html')

def auto_bid(request):
    return render(request, 'main/pages/auto_bid.html')

@login_required
def mypage(request):
    profile = None
    try:
        # Get the profile associated with the logged-in user
        profile = request.user.profile 
    except Profile.DoesNotExist:
        # Handle cases where profile might not exist (e.g., for superuser or older accounts)
        # Optionally create one here, or pass None to the template
        pass 
        
    context = {
        'profile': profile
        # 'user' is automatically available in templates if using RequestContext
    }
    return render(request, 'main/pages/mypage.html', context)

def bidform(request):
    context = {}
    
    case_number = request.GET.get('case_number')
    
    if case_number:
        try:
            case = get_object_or_404(AuctionCase, case_number=case_number)
            item_details = AuctionItem.objects.filter(case_number=case).first()
            
            if item_details:
                # 가장 최근 스케줄에서 매각기일 가져오기
                from app.models import AuctionSchedule
                latest_schedule = AuctionSchedule.objects.filter(
                    auction_item=item_details
                ).order_by('-round_number').first()
                
                case_info = {
                    'case_number': case.case_number,
                    'case_name': case.case_name,
                    'court_name': case.court_name,
                    'min_bid_price': case.minimum_bid_price or item_details.valuation_amount,
                    'auction_date': latest_schedule.auction_date if latest_schedule else item_details.auction_date
                }
                
                # 보증금 계산 (최저매각가격의 10%)
                try:
                    min_price_str = case_info['min_bid_price'] or "0"
                    min_price_str = ''.join(c for c in min_price_str if c.isdigit() or c == '.')
                    min_price = float(min_price_str)
                    deposit_amount = int(min_price * 0.1)
                except (ValueError, TypeError):
                    deposit_amount = 0
                
                # 사건번호에서 연도와 순번 추출
                import re
                case_match = re.match(r'(\d{4})타경(\d+)', case_number)
                if case_match:
                    case_year = case_match.group(1)
                    case_sequence = case_match.group(2)
                else:
                    if '타경' in case_number:
                        parts = case_number.split('타경')
                        case_year = parts[0] if len(parts) > 1 else ""
                        case_sequence = parts[1] if len(parts) > 1 else ""
                    else:
                        case_year = ""
                        case_sequence = ""
                
                context.update({
                    'case_info': case_info,
                    'deposit_amount': deposit_amount,
                    'min_bid_price': case_info['min_bid_price'],
                    'case_year': case_year,
                    'case_sequence': case_sequence,
                    'has_case_info': True
                })
        except (AuctionCase.DoesNotExist, AuctionItem.DoesNotExist):
            pass
    
    return render(request, 'main/pages/bidform.html', context)

def bid_submit(request):
    if request.method == 'POST':
        # 폼 처리 로직
        print(request.POST)  # 임시: 콘솔에 데이터 출력
        return redirect('bidform')  # 제출 후 다시 폼 페이지로 이동
    return redirect('bidform')  # GET으로 접근하면 다시 폼 페이지로

@login_required
def charge(request):
    profile = None
    if hasattr(request.user, 'profile'):
        profile = request.user.profile
    else:
        # Handle case where profile doesn't exist, maybe create it?
        # For now, redirect or show an error
        pass # Or redirect('some_error_page')

    if request.method == 'POST':
        amount = int(request.POST.get('amount'))
        if profile:
             profile.balance += amount
             profile.save()
        return redirect('charge')

    return render(request, 'main/pages/charge.html', {'balance': profile.balance if profile else 0})

def property_detail(request, case_number):
    try:
        case = get_object_or_404(AuctionCase, case_number=case_number)
        item_details = AuctionItem.objects.filter(case_number=case).first()
        
        claim_distribution = ClaimDistribution.objects.filter(case_number=case).first()
        property_listings = PropertyListing.objects.filter(case_number=case)
        interested_parties = AuctionParty.objects.filter(case_number=case)
        
        property_info = {
            'case_number': case.case_number if case else None,
            'case_name': case.case_name if case else None,
            'court': case.court_name if case else None,
            'receipt_date': case.filing_date if case else None,
            'responsible_dept': case.responsible_dept if case else None,
            'claim_amount': case.claim_amount if case else None,
            'appeal_status_display': '항고' if case and case.appeal_status else '미항고',
            'min_bid_price': case.minimum_bid_price if case else item_details.valuation_amount,
            'specification_url': item_details.item_spec_url
        }
        
        location_info = {
            'location': claim_distribution.location if claim_distribution else None,
            'claim_deadline': claim_distribution.claim_deadline if claim_distribution else None,
            'case_number': case.case_number if case else None
        }
        
        document_urls = {
            'specification_url': item_details.item_spec_url
        }
        
        # 입찰 내역 현황 - AuctionSchedule 사용
        bidding_history = []
        
        # AuctionSchedule에서 회차별 정보 가져오기
        from app.models import AuctionSchedule
        schedules = AuctionSchedule.objects.filter(auction_item=item_details).order_by('round_number')
        
        for schedule in schedules:
            # 실제 저장된 minimum_price 사용 (tsLwsDspslPrc 값)
            min_price = schedule.minimum_price if schedule.minimum_price else 0
            
            # 보증금 계산 (최저매각가격의 10%)
            deposit_amount = int(min_price * 0.1) if min_price > 0 else 0
            
            # 상태 결정
            if schedule.result_status:
                status = schedule.result_status
            elif item_details.auction_failures >= schedule.round_number:
                status = '유찰'
            else:
                status = '진행중'
            
            bidding_history.append({
                'id': schedule.round_number,
                'link_text': f"{case.case_number} {schedule.round_number}차 입찰",
                'type': f'{schedule.round_number}차 입찰',
                'min_price': f"{int(min_price):,}" if min_price > 0 else item_details.valuation_amount,
                'status': status,
                'price_details': f"{item_details.valuation_amount} / {int(min_price):,} / {int(valuation_amount * deposit_ratio):,}",
                'auction_date': schedule.auction_date,
                'due_date': schedule.decision_date
            })
        
        # 이미지 경로 준비
        image_paths = []
        if item_details.item_image_url:
            for url in item_details.item_image_url.split(','):
                if url.strip():
                    image_paths.append(url.strip())
        
        context = {
            'property_id': case_number,
            'property_info': property_info,
            'item_details': item_details,
            'case': case,
            'location_info': location_info,
            'document_urls': document_urls,
            'bidding_history': bidding_history,
            'building_details': property_listings,
            'interested_parties': interested_parties,
            'image_paths': image_paths,
            'naver_maps_client_id': getattr(settings, 'NAVER_MAPS_CLIENT_ID', '')
        }
        
        return render(request, 'main/pages/property_detail.html', context)
        
    except AuctionItem.DoesNotExist:
        return redirect('index')

def get_favorite_properties(request):
    try:
        from main.models import FavoriteProperty 
        favorites = FavoriteProperty.objects.all()
        data = [
            {'case_number': fav.case_number, 'usage': fav.usage}
            for fav in favorites
        ]
        return JsonResponse({'success': True, 'favorites': data})
    except:
        return JsonResponse({'success': True, 'favorites': []})

# Add missing view functions referenced in templates
def bid_history(request):
    return render(request, 'main/pages/bid_history.html')

def refund(request):
    return render(request, 'main/pages/refund.html')

def favorites(request):
    return render(request, 'main/pages/favorites.html')

def update_wallet(request):
    if request.method == 'POST':
        # Handle wallet update logic
        return redirect('mypage')
    return redirect('mypage')

# Remove custom login/logout views - use allauth instead