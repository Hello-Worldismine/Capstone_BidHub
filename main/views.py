# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Profile
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from main.models import FavoriteProperty
from app.models import AuctionItem, AuctionCase
import json
from decimal import Decimal # Import Decimal
from django.templatetags.static import static # Import static function
from django.conf import settings # Import settings
from app.models import AuctionItem, AuctionCase, ClaimDistribution, PropertyListing, AuctionParty, BuildingDetail, AuctionSchedule
from django.utils import timezone # Add timezone import
from django.db.models import Q, Prefetch
from allauth.account.forms import LoginForm
from django.template.response import TemplateResponse
from app.models import BidLog  # 필요한 모델 import
import requests
from datetime import datetime, timedelta


#아이디 찾기 관련 추가
from django.contrib.auth import get_user_model
User = get_user_model()

#검색 관련 추가
from datetime import date
from .models import AuctionItem  # 실제 모델명에 맞게 수정하세요
from django.core.paginator import Paginator


GRAPHQL_URL = "https://api.studio.thegraph.com/query/111711/capstone/version/latest"

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
            
            # 건물 상세정보 가져오기 (BuildingDetail 모델 사용)
            building_details = []
            try:
                building_details_qs = BuildingDetail.objects.filter(auction_item=item_details).order_by('sequence')
                building_details = list(building_details_qs)
            except Exception as e:
                print(f"❌ BuildingDetail 조회 오류: {e}")
                building_details = []
            
            # 감정평가액 (기준 가격)
            valuation_amount = 0
            if item_details and item_details.valuation_amount:
                valuation_amount = int(item_details.valuation_amount.replace(',', '')) if isinstance(item_details.valuation_amount, str) else item_details.valuation_amount
            
            # AuctionSchedule에서 현재 매물(item_details)의 id와 정확히 매칭되는 스케줄만 조회
            from app.models import AuctionSchedule
            from django.utils import timezone
            
            # 중요: auction_item 필드를 통해 정확한 매물의 스케줄만 조회
            schedules = AuctionSchedule.objects.filter(
                auction_item_id=item_details.id  # auction_item_id와 item_details.id를 정확히 매칭
            ).order_by('round_number')
            
            print(f"🔍 매물 ID: {item_details.id}, 사건번호: {case_number}")
            print(f"📋 해당 매물의 스케줄 개수: {schedules.count()}")
            
            # 현재 진행중인 매각기일의 최저매각가격 찾기
            current_min_price = valuation_amount  # 기본값
            current_round = 1
            
            now = timezone.now().date()
            
            for schedule in schedules:
                print(f"📅 스케줄 정보 - 회차: {schedule.round_number}, 타입: {schedule.schedule_type}, 가격: {schedule.minimum_price}")
                
                # 매각기일이고 아직 지나지 않은 경우
                if (schedule.schedule_type == '매각기일' and 
                    schedule.auction_date and 
                    schedule.auction_date.date() >= now and
                    schedule.minimum_price and 
                    schedule.minimum_price > 0):
                    
                    current_min_price = schedule.minimum_price  # tsLwsDspslPrc 값 사용
                    current_round = schedule.round_number
                    print(f"✅ 현재 진행중인 매각기일 발견 - {current_round}차, 가격: {current_min_price}")
                    break
                
                # 과거 매각기일 중 가장 최근 회차 확인 (다음 회차 예측용)
                elif (schedule.schedule_type == '매각기일' and 
                      schedule.auction_date and 
                      schedule.auction_date.date() < now):
                    current_round = schedule.round_number + 1  # 다음 회차
            
            # 만약 진행중인 매각기일을 찾지 못했다면 감정평가액 사용
            if current_min_price == valuation_amount and schedules.exists():
                # 가장 최근 스케줄의 minimum_price 사용 (해당 매물의 것만)
                latest_schedule = schedules.filter(
                    schedule_type='매각기일',
                    minimum_price__gt=0
                ).first()
                
                if latest_schedule:
                    current_min_price = latest_schedule.minimum_price
                    current_round = latest_schedule.round_number
                    print(f"📌 최신 스케줄 사용 - {current_round}차, 가격: {current_min_price}")
            
            # 감정평가액 대비 비율 계산
            price_ratio = 100
            if valuation_amount > 0:
                price_ratio = round((current_min_price / valuation_amount) * 100)
            
            # 🔧 법원 정보 정확히 설정
            court_name = case.court_name if case and case.court_name else "법원 정보 없음"
            print(f"🏛️ 법원 정보: {court_name}")
            
            property_info = {
                'case_number': case.case_number if case else None,
                'case_name': case.case_name if case else None,
                'property_name': item_details.property_name if item_details else None,
                'court': court_name,  # 정확한 법원 정보 사용
                'court_name': court_name,  # 추가로 court_name도 제공
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
            
            # 📍 주소 정보를 item_details의 property_address를 우선 사용하도록 수정
            location_address = None
            if item_details:
                # AuctionItem의 get_formatted_address 메서드 사용
                location_address = item_details.get_formatted_address()
            
            # 만약 AuctionItem에 주소가 없으면 ClaimDistribution의 location 사용
            if location_address == "주소 정보 없음" and claim_distribution and claim_distribution.location:
                location_address = claim_distribution.location
            
            location_info = {
                'location': location_address,
                'claim_deadline': claim_distribution.claim_deadline if claim_distribution else None,
                'case_number': case.case_number if case else None
            }
            
            document_urls = {
                'specification_url': item_details.item_spec_url if item_details else None
            }
            
            # 입찰 내역 현황 - 해당 매물의 AuctionSchedule만 사용
            bidding_history = []
            
            if item_details and item_details.valuation_amount:
                try:
                    val_amount_str = item_details.valuation_amount or "0"
                    val_amount_str = ''.join(c for c in val_amount_str if c.isdigit() or c == '.')
                    valuation_amount = float(val_amount_str)
                except (ValueError, TypeError):
                    valuation_amount = 0
                
            # 해당 매물의 스케줄만 가져오기 (auction_item_id로 정확히 매칭)
            if item_details:
                schedules = AuctionSchedule.objects.filter(
                    auction_item_id=item_details.id  # 정확한 매물 ID로 필터링
                ).order_by('round_number')
                
                print(f"🔍 입찰 내역용 스케줄 조회 - 매물 ID: {item_details.id}, 스케줄 수: {schedules.count()}")
                
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
                    
                    print(f"📊 입찰 내역 추가 - 회차: {schedule.round_number}, 가격: {min_price}, 상태: {status}")
            
            # 이미지 경로 준비
            image_paths = []
            if item_details and item_details.item_image_url:
                for url in item_details.item_image_url.split(','):
                    if url.strip():
                        image_paths.append(url.strip())
            
            user_wallet_address = ""
            if request.user.is_authenticated:
                user_wallet_address = request.user.profile.wallet_address  # 또는 적절한 위치
            
            context = {
                'property_id': case_number,
                'property_info': property_info,
                'item_details': item_details,
                'case': case,
                'location_info': location_info,
                'document_urls': document_urls,
                'bidding_history': bidding_history,
                'building_details': building_details,  # 수정된 부분: BuildingDetail 모델 데이터 사용
                'interested_parties': interested_parties,
                'image_paths': image_paths,
                'user_wallet_address': user_wallet_address,
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
                # tender 뷰와 동일한 로직으로 현재 최저매각가격 찾기
                from app.models import AuctionSchedule
                from django.utils import timezone
                
                schedules = AuctionSchedule.objects.filter(auction_item=item_details).order_by('round_number')
                
                # 감정평가액 (기준 가격)
                valuation_amount = 0
                if item_details.valuation_amount:
                    try:
                        if isinstance(item_details.valuation_amount, str):
                            valuation_amount = int(item_details.valuation_amount.replace(',', ''))
                        else:
                            valuation_amount = int(item_details.valuation_amount)
                    except (ValueError, TypeError):
                        valuation_amount = 0
                
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
                
                # 가장 최근 매각기일 가져오기 (날짜 표시용)
                latest_schedule = AuctionSchedule.objects.filter(
                    auction_item=item_details,
                    schedule_type='매각기일'
                ).order_by('-round_number').first()
                
                # 현재 시간과 입찰 가능 시간 계산
                current_time = timezone.now()
                auction_start_time = None
                auction_end_time = None
                
                # 가장 최근 매각기일 가져오기
                latest_schedule = AuctionSchedule.objects.filter(
                    auction_item=item_details,
                    schedule_type='매각기일'
                ).order_by('-round_number').first()
                
                if latest_schedule and latest_schedule.auction_date:
                    auction_start_time = latest_schedule.auction_date
                    auction_end_time = auction_start_time + timedelta(hours=1)
                elif item_details.auction_date:
                    auction_start_time = item_details.auction_date
                    auction_end_time = auction_start_time + timedelta(hours=1)
                
                # 입찰 가능 여부 확인
                bidding_available = False
                if auction_start_time and auction_end_time:
                    bidding_available = auction_start_time <= current_time <= auction_end_time
                
                case_info = {
                    'case_number': case.case_number,
                    'case_name': case.case_name,
                    'court_name': case.court_name,
                    'property_name': item_details.property_name,
                    'min_bid_price': f"{current_min_price:,}",
                    'min_bid_price_raw': current_min_price,
                    'valuation_amount': f"{valuation_amount:,}",
                    'current_round': current_round,
                    'auction_date': latest_schedule.auction_date if latest_schedule else item_details.auction_date,
                    'auction_start_time': auction_start_time,
                    'auction_end_time': auction_end_time,
                    'bidding_available': bidding_available
                }
                
                context.update({
                    'case_info': case_info,
                    'current_time': current_time,
                    # ...existing context...
                })
                
        except (AuctionCase.DoesNotExist, AuctionItem.DoesNotExist):
            context.update({
                'error_message': "해당 사건 정보를 찾을 수 없습니다.",
                'has_case_info': False
            })
    else:
        context.update({
            'error_message': "사건번호가 필요합니다.",
            'has_case_info': False
        })
    
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
        
        # 감정평가액 계산
        valuation_amount = 0
        if item_details and item_details.valuation_amount:
            try:
                val_amount_str = item_details.valuation_amount or "0"
                val_amount_str = ''.join(c for c in val_amount_str if c.isdigit() or c == '.')
                valuation_amount = float(val_amount_str)
            except (ValueError, TypeError):
                valuation_amount = 0
        
        # 보증금 비율 (10%)
        deposit_ratio = 0.1
        
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
            'naver_maps_client_id': getattr(settings, 'NAVER_MAPS_CLIENT_ID', ''),
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

#로그인관련view
def join(request):
    return render(request, 'account/signup.html')
def login(request):
    form = LoginForm()
    return TemplateResponse(request, 'account/login.html', {'form': form})


def update_wallet(request):
    if request.method == 'POST':
        wallet = request.POST.get('wallet_address', '')
        profile = request.user.profile
        profile.wallet_address = wallet
        profile.save()
    return redirect('mypage')  # 저장 후 마이페이지로 리디렉션
#아이디찾기 관련 views
def find_id(request):
    found_username = None
    error_message = None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        phone = request.POST.get('phone', '').strip()

        try:
            user = User.objects.get(username=name, phone=phone) 
            found_username = user.username
        except User.DoesNotExist:
            error_message = '입력하신 정보와 일치하는 계정을 찾을 수 없습니다.'

    return render(request, 'account/find_id.html', {
        'found_username': found_username,
        'error_message': error_message
    })


#오늘의경매 관련 Views
def today_bid(request):
    """오늘의 경매"""
    today = date.today()
    items = AuctionItem.objects.filter(
        auction_date__date=today
    ).select_related('case_number').order_by('auction_date')

    # 페이지네이션 (20개씩)
    paginator = Paginator(items, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'main/pages/today_bid.html', context)

#주간경매공고 관련 views
def week_bid(request):
    """주간 경매 공고"""
    today = date.today()
    end_date = today + timedelta(days=7)
    items = AuctionItem.objects.filter(
        auction_date__date__range=(today, end_date)
    ).select_related('case_number').order_by('auction_date')

    # 페이지네이션 (20개씩)
    paginator = Paginator(items, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
    }
    return render(request, 'main/pages/week_bid.html', context)


def search_cases_api(request):
    """사건 검색 API (AJAX용) - 법원 필수, 연도/번호 선택"""
    if request.method != 'GET':
        return JsonResponse({'error': 'GET 요청만 허용됩니다.'}, status=405)
    
    court = request.GET.get('court', '').strip()
    year = request.GET.get('year', '').strip()
    number = request.GET.get('number', '').strip()
    
    # 법원은 필수 선택
    if not court:
        return JsonResponse({
            'error': '법원을 선택해주세요.',
            'results': []
        }, status=400)
    
    try:
        # 입력된 필드만 검증
        if year:
            year_int = int(year)
            if year_int < 2000 or year_int > 2030:
                raise ValueError("연도 범위 오류")
        
        if number:
            number_int = int(number)
            if number_int <= 0:
                raise ValueError("사건번호 오류")
            
    except ValueError:
        return JsonResponse({
            'error': '올바른 형식으로 입력해주세요.',
            'results': []
        }, status=400)
    
    try:
        # 기본 법원 검색 조건
        query = Q(court_name__icontains=court)
        
        # 연도 조건 추가 (선택사항)
        if year:
            query &= Q(case_number__icontains=year)
        
        # 사건번호 조건 추가 (선택사항)
        if number:
            query &= Q(case_number__icontains=number)
        
        # 데이터베이스 검색 - 올바른 관계명 사용
        cases = AuctionCase.objects.filter(query).prefetch_related(
            'auctionitem_set'
        ).distinct()[:50]
        
        # JSON 형태로 변환
        results = []
        for case in cases:
            # 관련 경매 물건 정보
            auction_items = case.auctionitem_set.all()
            
            case_data = {
                'id': case.case_number,  # case_number를 id로 사용
                'case_number': case.case_number,
                'case_name': case.case_name,
                'court': case.court_name,
                'auctionitem_set': [{
                    'id': item.id,
                    'item_number': item.item_number,
                    'property_name': item.property_name,
                    'valuation_amount': str(item.valuation_amount) if item.valuation_amount else None,
                    'auction_failures': item.auction_failures,
                    'item_note': item.item_note,
                    'item_purpose': item.item_purpose,
                    'auction_date': item.auction_date.isoformat() if item.auction_date else None,
                } for item in auction_items],
                # 스케줄 정보를 아이템별로 가져오기
                'schedules': []
            }
            
            # 각 아이템의 스케줄 정보 수집
            for item in auction_items:
                schedules = item.schedules.all()
                for schedule in schedules:
                    case_data['schedules'].append({
                        'id': schedule.id,
                        'schedule_type': schedule.schedule_type,
                        'auction_date': schedule.auction_date.isoformat() if schedule.auction_date else None,
                        'minimum_price': str(schedule.minimum_price) if schedule.minimum_price else None,
                        'round_number': schedule.round_number,
                        'result_status': schedule.result_status,
                    })
            
            results.append(case_data)
        
        return JsonResponse({
            'success': True,
            'results': results,
            'count': len(results),
            'message': f'{len(results)}건의 검색 결과를 찾았습니다.'
        })
        
    except Exception as e:
        import traceback
        print(f"Search error: {e}")
        print(traceback.format_exc())
        return JsonResponse({
            'error': f'검색 중 오류가 발생했습니다: {str(e)}',
            'results': []
        }, status=500)

def fsearch(request):
    """빠른 검색 페이지"""
    context = {
        'title': '빠른검색',
    }
    
    # GET 파라미터가 있으면 초기 검색 수행
    court = request.GET.get('court', '').strip()
    year = request.GET.get('year', '').strip()
    number = request.GET.get('number', '').strip()
    
    if court:  # 법원이 선택된 경우에만 검색
        try:
            # 기본 법원 검색 조건
            query = Q(court_name__icontains=court)
            
            # 연도 조건 추가 (선택사항)
            if year:
                query &= Q(case_number__icontains=year)
            
            # 사건번호 조건 추가 (선택사항)
            if number:
                query &= Q(case_number__icontains=number)
            
            cases = AuctionCase.objects.filter(query).prefetch_related(
                'auctionitem_set'
            )[:50]
            
            context.update({
                'search_results': cases,
                'search_performed': True,
                'search_params': {
                    'court': court,
                    'year': year,
                    'number': number
                }
            })
            
        except Exception as e:
            context.update({
                'search_error': f'검색 중 오류가 발생했습니다: {str(e)}',
                'search_performed': True
            })
    
    return render(request, 'main/pages/fsearch.html', context)


def csearch(request):
    """조건검색 페이지 및 필터링 처리"""
    from django.core.paginator import Paginator
    from django.db.models import Q
    import logging
    
    logger = logging.getLogger(__name__)
    
    # 기본 쿼리셋
    auction_cases = AuctionCase.objects.select_related().prefetch_related('auctionitem_set').all()
    
    # 필터 파라미터 받기 (AJAX 요청에서도 제대로 받을 수 있도록)
    item_types = request.GET.getlist('item_types')  # 복수 선택 가능
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    failure_count = request.GET.get('failure_count')
    
    # 디버깅용 로그
    print(f"Received filters - item_types: {item_types}, min_price: {min_price}, max_price: {max_price}, failure_count: {failure_count}")
    print(f"Request method: {request.method}")
    print(f"Request headers: {dict(request.headers)}")
    print(f"Query string: {request.GET}")
    
    # 필터 적용 여부 확인
    filters_applied = bool(item_types or min_price or max_price or failure_count)
    
    # 초기 매물 수
    initial_count = auction_cases.count()
    print(f"Initial auction cases count: {initial_count}")
    
    # 물건 종류 필터
    if item_types:
        # AuctionItem의 property_type 필드로 필터링
        type_query = Q()
        for item_type in item_types:
            type_query |= Q(auctionitem__property_type__icontains=item_type)
        auction_cases = auction_cases.filter(type_query).distinct()
        print(f"After item type filter: {auction_cases.count()}")
    
    # 가격 필터 (감정평가액 기준) - Python에서 직접 필터링
    if min_price or max_price:
        try:
            min_price_val = int(min_price) if min_price else 0
            max_price_val = int(max_price) if max_price else float('inf')
            
            print(f"Applying price filter: {min_price_val} <= price <= {max_price_val}")
            
            # 18억 이상인 경우 상한선 제거
            if max_price_val >= 1800000000:
                max_price_val = float('inf')
            
            filtered_cases = []
            for case in auction_cases:
                case_items = case.auctionitem_set.all()
                for item in case_items:
                    if item.valuation_amount:
                        try:
                            # 문자열에서 쉼표 제거 후 정수 변환
                            if isinstance(item.valuation_amount, str):
                                amount = int(item.valuation_amount.replace(',', ''))
                            else:
                                amount = int(item.valuation_amount)
                            
                            # 범위 내에 있으면 케이스 추가
                            if min_price_val <= amount <= max_price_val:
                                if case not in filtered_cases:
                                    filtered_cases.append(case)
                                break  # 한 아이템이라도 조건에 맞으면 케이스 포함
                        except (ValueError, TypeError):
                            continue
            
            # 필터링된 케이스들의 ID로 쿼리셋 재구성
            case_ids = [case.case_number for case in filtered_cases]
            auction_cases = AuctionCase.objects.filter(case_number__in=case_ids).select_related().prefetch_related('auctionitem_set')
            
            print(f"After price filter: {auction_cases.count()}")
            
        except (ValueError, TypeError) as e:
            print(f"Error in price filtering: {e}")
    
    # 유찰횟수 필터
    if failure_count:
        print(f"Applying failure_count filter: {failure_count}")
        if failure_count == "최초경매":
            auction_cases = auction_cases.filter(auctionitem__auction_failures=0)
        elif failure_count == "유찰 1회":
            auction_cases = auction_cases.filter(auctionitem__auction_failures=1)
        elif failure_count == "유찰 2회":
            auction_cases = auction_cases.filter(auctionitem__auction_failures=2)
        elif failure_count == "3회 이상":
            auction_cases = auction_cases.filter(auctionitem__auction_failures__gte=3)
        print(f"After failure_count filter: {auction_cases.count()}")
    
    # 중복 제거 및 정렬 - filing_date로 정렬 (최신순)
    auction_cases = auction_cases.distinct().order_by('-filing_date', '-case_number')
    
    final_count = auction_cases.count()
    print(f"Final count after distinct and ordering: {final_count}")
    
    # 실제 데이터 샘플 확인 (처음 5개)
    if final_count > 0:
        sample_cases = auction_cases[:5]
        for case in sample_cases:
            items = case.auctionitem_set.all()
            for item in items:
                print(f"Case: {case.case_number}, Valuation: {item.valuation_amount}")
    
    # 페이징 처리
    paginator = Paginator(auction_cases, 20)  # 페이지당 20개
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        # 올바른 변수명으로 전달
        'search_results': page_obj.object_list,  # 실제 객체 리스트
        'page_obj': page_obj,  # 페이지 객체
        'total_count': paginator.count,  # 전체 개수
        'current_page': page_obj.number,
        'total_pages': paginator.num_pages,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'filters_applied': filters_applied,
        'search_performed': True,
        'filter_params': {
            'item_types': ', '.join(item_types) if item_types else None,
            'min_price': min_price,
            'max_price': max_price,
            'failure_count': failure_count,
        }
    }
    
    return render(request, 'main/pages/csearch.html', context)

def bid_history(request):
    user_address = request.user.profile.wallet_address.lower()
    
    bid_logs = BidLog.objects.filter(bidder_address__iexact=user_address)
    bid_rows = []
    
    for log in bid_logs:
        trade_num = log.trade_num
        bid_amount = log.bid_amount or "경매 마감 후 공개"

        trade_str = str(trade_num)
        year = trade_str[:4]
        suffix = trade_str[4:]
        case_number = f"{year}타경{suffix}"

        graphql_query = f"""
        {{
          putSecs(where: {{tradeNum: "{trade_num}", bidder: "{user_address}"}}) {{
            security
          }}
          refundSecurities(where: {{tradeNum: "{trade_num}", bidder: "{user_address}"}}) {{
            blockTimestamp
          }}
          bidWins(where: {{tradeNum: "{trade_num}"}}) {{
            winner
          }}
        }}
        """
        headers = {"Content-Type": "application/json"}
        res = requests.post(GRAPHQL_URL, json={'query': graphql_query}, headers=headers)

        data = res.json().get("data", {})
        security_data = data.get("putSecs", [])
        if security_data:
            raw_wei = int(security_data[0]["security"])
            eth = raw_wei / 1e18
            krw = eth * 10_000_000_000
            security = round(krw)  
        else:
            security = 0

        refund_data = data.get("refundSecurities", [])
        if refund_data:
            refund_status = "완료"
            refund_date = datetime.fromtimestamp(int(refund_data[0]["blockTimestamp"])).strftime("%Y-%m-%d")
        else:
            refund_status = "처리중"
            refund_date = "-"

        win_data = data.get("bidWins", [])
        is_winner = win_data and win_data[0]["winner"].lower() == user_address

        bid_rows.append({
            "case_number": case_number,
            "bid_amount": f"{bid_amount:,}" if isinstance(bid_amount, int) else bid_amount,
            "security": f"{security:,}원",
            "refund_status": refund_status,
            "refund_date": refund_date,
            "is_winner": is_winner
        })

    return render(request, "main/pages/bid_history.html", {"bid_rows": bid_rows})


def chat_view(request):
    return render(request, 'chatbot/chat.html') # 챗봇상담 페이지

def result(request):
    return render(request, 'main/pages/result.html')

def region_result(request):
    return render(request, 'main/pages/region_result.html')

from django.utils import timezone
from datetime import timedelta
from rest_framework.decorators import api_view


def get_bid_events(request):
    trade_num = request.GET.get("trade_num")
    if not trade_num:
        return JsonResponse({"error": "trade_num parameter is required"}, status=400)

    query = {
        "query": f"""
        {{
          bidEnters(where: {{ tradeNum: "{trade_num}" }}) {{
            bidder
            amount
            security
            bidtime
          }}
        }}
        """
    }

    try:
        res = requests.post(GRAPHQL_URL, json=query)
        res.raise_for_status()
        data = res.json()
        events = data.get("data", {}).get("bidEnters", [])

        # 정렬: amount 내림차순, 같은 경우 bidtime 내림차순
        sorted_events = sorted(
            events,
            key=lambda e: (-int(e["amount"]), -int(e["bidtime"]))
        )

        return JsonResponse({"bids": sorted_events})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    

    # -------------------- 실시간 상담 기능 --------------------

import uuid
from consult_app.active_rooms import active_rooms, room_assignments  # consult_app에서 복사 필요
from django.http import JsonResponse

# 실시간 방 목록 API
def consult_active_rooms_api(request):
    return JsonResponse({'rooms': list(active_rooms)})

# 사용자 채팅방 입장
def consult_user_room(request, room_name):
    if room_name not in active_rooms:
        active_rooms.append(room_name)
    return render(request, 'consult_app/room.html', {
        'room_name': room_name,
        'is_agent': False
    })

# 상담원 채팅방 입장
def consult_agent_room(request, room_name):
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

# 사용자 시작화면 - 법원 선택 화면
def consult_index(request):
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
def consult_enter_court_room(request):
    selected_court = request.POST.get('court')
    if selected_court in COURT_CODE_MAP:
        base = COURT_CODE_MAP[selected_court]
        suffix = str(uuid.uuid4())[:8]
        room_id = f"{base}-{suffix}"
        return redirect(f'/consult_app/{room_id}/')
    return redirect('/consult_app/')

# 상담원 대시보드
def consult_agent_dashboard(request):
    return render(request, 'consult_app/agent_dashboard.html', {
        'active_rooms': active_rooms
    })

# 상담 종료 처리
def consult_complete_chat(request, room_name):
    if room_name in active_rooms:
        active_rooms.remove(room_name)
        return JsonResponse({'status': 'success', 'message': '방 제거됨'})
    else:
        return JsonResponse({'status': 'error', 'message': '해당 방 없음'})

# 방 이름용 법원 코드 맵
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


@login_required(login_url='account_login') 
def bid_history(request):
    return render(request, 'main/pages/bid_history.html')

@login_required(login_url='account_login') 
def favlist(request):
    favorite_list = FavoriteProperty.objects.filter(user=request.user).select_related('auction_item')
    return render(request, 'main/pages/favlist.html', {'favorite_list': favorite_list})

@login_required(login_url='account_login') 
def bidform(request):
    return render(request, 'main/pages/bidform.html')

@login_required
def mypage(request):
    user = request.user
    
    # Profile 모델이 있는지 확인하고 없으면 생성
    try:
        user_profile = user.profile
    except:
        # Profile이 없으면 User 모델의 데이터로 생성
        from accounts.models import Profile
        user_profile = Profile.objects.create(
            user=user,
            name=getattr(user, 'name', ''),
            id_number=getattr(user, 'id_number', ''),
            phone=getattr(user, 'phone', ''),
            address=getattr(user, 'address', ''),
        )
    
    # 컨텍스트 데이터 준비
    context = {
        'user': user,
        'user_profile': user_profile,
        'profile': {
            'name': user_profile.name or getattr(user, 'name', '정보 없음'),
            'identifier': user_profile.id_number or getattr(user, 'id_number', '정보 없음'),
            'phone': user_profile.phone or getattr(user, 'phone', '정보 없음'),
            'address': user_profile.address or getattr(user, 'address', '정보 없음'),
        }
    }
    
    return render(request, 'main/pages/mypage.html', context)

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        
        # User 모델 업데이트
        if hasattr(user, 'name'):
            user.name = request.POST.get('name', '')
        if hasattr(user, 'id_number'):
            user.id_number = request.POST.get('id_number', '')
        if hasattr(user, 'phone'):
            user.phone = request.POST.get('phone', '')
        if hasattr(user, 'address'):
            user.address = request.POST.get('address', '')
        user.save()
        
        # Profile 모델 업데이트
        try:
            profile = user.profile
            profile.name = request.POST.get('name', '')
            profile.id_number = request.POST.get('id_number', '')
            profile.phone = request.POST.get('phone', '')
            profile.address = request.POST.get('address', '')
            profile.save()
        except:
            # Profile이 없으면 생성
            from accounts.models import Profile
            Profile.objects.create(
                user=user,
                name=request.POST.get('name', ''),
                id_number=request.POST.get('id_number', ''),
                phone=request.POST.get('phone', ''),
                address=request.POST.get('address', ''),
            )
    
    return redirect('mypage')

@login_required
@csrf_exempt
def add_favorite(request):
    """즐겨찾기 추가"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            case_number = data.get('case_number')
            
            if not case_number:
                return JsonResponse({'success': False, 'message': '사건번호가 필요합니다.'})
            
            # AuctionItem 찾기
            try:
                auction_case = AuctionCase.objects.get(case_number=case_number)
                auction_item = AuctionItem.objects.filter(case_number=auction_case).first()
                
                if not auction_item:
                    return JsonResponse({'success': False, 'message': '해당 매물을 찾을 수 없습니다.'})
                
                # 이미 즐겨찾기에 있는지 확인
                favorite, created = FavoriteProperty.objects.get_or_create(
                    user=request.user,
                    auction_item=auction_item,
                    defaults={
                        'case_number': case_number,
                        'usage': auction_item.property_type or '정보없음'
                    }
                )
                
                if created:
                    return JsonResponse({'success': True, 'message': '즐겨찾기에 추가되었습니다.'})
                else:
                    return JsonResponse({'success': False, 'message': '이미 즐겨찾기에 있습니다.'})
                    
            except AuctionCase.DoesNotExist:
                return JsonResponse({'success': False, 'message': '사건을 찾을 수 없습니다.'})
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': '잘못된 요청 방법입니다.'})

@login_required
@csrf_exempt
def remove_favorite(request, item_id):
    """즐겨찾기 제거"""
    if request.method == 'POST':
        try:
            # item_id가 FavoriteProperty의 ID인 경우
            if item_id.isdigit():
                favorite = FavoriteProperty.objects.filter(
                    id=item_id, 
                    user=request.user
                ).first()
            else:
                # item_id가 case_number인 경우
                favorite = FavoriteProperty.objects.filter(
                    case_number=item_id, 
                    user=request.user
                ).first()
            
            if favorite:
                favorite.delete()
                return JsonResponse({'success': True, 'message': '즐겨찾기에서 제거되었습니다.'})
            else:
                return JsonResponse({'success': False, 'message': '즐겨찾기 항목을 찾을 수 없습니다.'})
                
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': '잘못된 요청 방법입니다.'})

@login_required
@csrf_exempt
def toggle_favorite(request):
    """즐겨찾기 토글 (추가/제거)"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            case_number = data.get('case_number')
            
            if not case_number:
                return JsonResponse({'success': False, 'message': '사건번호가 필요합니다.'})
            
            # 기존 즐겨찾기 확인
            existing_favorite = FavoriteProperty.objects.filter(
                user=request.user,
                case_number=case_number
            ).first()
            
            if existing_favorite:
                # 제거
                existing_favorite.delete()
                return JsonResponse({
                    'success': True, 
                    'action': 'removed',
                    'message': '즐겨찾기에서 제거되었습니다.'
                })
            else:
                # 추가
                try:
                    auction_case = AuctionCase.objects.get(case_number=case_number)
                    auction_item = AuctionItem.objects.filter(case_number=auction_case).first()
                    
                    if not auction_item:
                        return JsonResponse({'success': False, 'message': '해당 매물을 찾을 수 없습니다.'})
                    
                    FavoriteProperty.objects.create(
                        user=request.user,
                        auction_item=auction_item,
                        case_number=case_number,
                        usage=auction_item.property_type or '정보없음'
                    )
                    
                    return JsonResponse({
                        'success': True, 
                        'action': 'added',
                        'message': '즐겨찾기에 추가되었습니다.'
                    })
                    
                except AuctionCase.DoesNotExist:
                    return JsonResponse({'success': False, 'message': '사건을 찾을 수 없습니다.'})
                    
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': '잘못된 요청입니다.'})
        except Exception as e:
            return JsonResponse({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})
    
    return JsonResponse({'success': False, 'message': '잘못된 요청 방법입니다.'})

@login_required
def check_favorite_status(request, case_number):
    """즐겨찾기 상태 확인"""
    try:
        is_favorite = FavoriteProperty.objects.filter(
            user=request.user,
            case_number=case_number
        ).exists()
        
        return JsonResponse({
            'success': True, 
            'is_favorite': is_favorite
        })
    except Exception as e:
        return JsonResponse({'success': False, 'message': f'오류가 발생했습니다: {str(e)}'})

@login_required
def favlist(request):
    """즐겨찾기 목록 페이지"""
    favorite_list = FavoriteProperty.objects.filter(
        user=request.user
    ).select_related('auction_item', 'auction_item__case_number').order_by('-created_at')
    
    return render(request, 'main/pages/favlist.html', {
        'favorite_list': favorite_list
    })
