from django.utils import timezone
from app.models import AuctionSchedule, BuildingDetail, ClaimDistribution, PropertyListing, AuctionParty
from .image_helper import get_property_images

def get_current_min_price_and_round(item_details, valuation_amount):
    """현재 진행중인 매각기일의 최저매각가격과 회차 반환"""
    
    schedules = AuctionSchedule.objects.filter(
        auction_item_id=item_details.id
    ).order_by('round_number')
    
    print(f"🔍 매물 ID: {item_details.id}, 스케줄 개수: {schedules.count()}")
    
    current_min_price = valuation_amount  # 기본값
    current_round = 1
    now = timezone.now().date()
    
    for schedule in schedules:
        print(f"📅 스케줄 - 회차: {schedule.round_number}, 타입: {schedule.schedule_type}, 가격: {schedule.minimum_price}")
        
        # 매각기일이고 아직 지나지 않은 경우
        if (schedule.schedule_type == '매각기일' and 
            schedule.auction_date and 
            schedule.auction_date.date() >= now and
            schedule.minimum_price and 
            schedule.minimum_price > 0):
            
            current_min_price = schedule.minimum_price
            current_round = schedule.round_number
            print(f"✅ 현재 진행중인 매각기일 - {current_round}차, 가격: {current_min_price}")
            break
        
        # 과거 매각기일 중 가장 최근 회차
        elif (schedule.schedule_type == '매각기일' and 
              schedule.auction_date and 
              schedule.auction_date.date() < now):
            current_round = schedule.round_number + 1
    
    # 진행중인 매각기일을 찾지 못했다면 가장 최근 스케줄 사용
    if current_min_price == valuation_amount and schedules.exists():
        latest_schedule = schedules.filter(
            schedule_type='매각기일',
            minimum_price__gt=0
        ).first()
        
        if latest_schedule:
            current_min_price = latest_schedule.minimum_price
            current_round = latest_schedule.round_number
            print(f"📌 최신 스케줄 사용 - {current_round}차, 가격: {current_min_price}")
    
    return current_min_price, current_round

def get_property_info(case, item_details, current_min_price, current_round, valuation_amount):
    """매물 기본 정보 딕셔너리 생성"""
    
    # 감정평가액 대비 비율 계산
    price_ratio = 100
    if valuation_amount > 0:
        price_ratio = round((current_min_price / valuation_amount) * 100)
    
    court_name = case.court_name if case and case.court_name else "법원 정보 없음"
    
    return {
        'case_number': case.case_number if case else None,
        'case_name': case.case_name if case else None,
        'property_name': item_details.property_name if item_details else None,
        'court': court_name,
        'court_name': court_name,
        'receipt_date': case.filing_date if case else None,
        'responsible_dept': case.responsible_dept if case else None,
        'claim_amount': case.claim_amount if case else None,
        'appeal_status_display': '항고' if case and case.appeal_status else '미항고',
        'min_bid_price': f"{current_min_price:,}",
        'current_round': current_round,
        'valuation_amount': f"{valuation_amount:,}",
        'price_ratio': price_ratio,
        'specification_url': item_details.item_spec_url if item_details else None
    }

def get_location_info(item_details, claim_distribution, case):
    """위치 정보 딕셔너리 생성"""
    
    location_address = None
    if item_details:
        location_address = item_details.get_formatted_address()
    
    # AuctionItem에 주소가 없으면 ClaimDistribution 사용
    if location_address == "주소 정보 없음" and claim_distribution and claim_distribution.location:
        location_address = claim_distribution.location
    
    return {
        'location': location_address,
        'claim_deadline': claim_distribution.claim_deadline if claim_distribution else None,
        'case_number': case.case_number if case else None
    }

def get_status_text(result_status):
    """결과 상태를 한글로 변환"""
    status_map = {
        'SUCCESS': '낙찰',
        'FAIL': '유찰',
        'PENDING': '진행중',
        'CANCELLED': '취소',
        None: '예정'
    }
    return status_map.get(result_status, '알 수 없음')

def get_bidding_history(item_details, case):
    """입찰 내역 현황 생성"""
    
    bidding_history = []
    
    if not item_details:
        return bidding_history
    
    schedules = AuctionSchedule.objects.filter(
        auction_item_id=item_details.id
    ).order_by('round_number')
    
    print(f"🔍 입찰 내역용 스케줄 조회 - 매물 ID: {item_details.id}, 스케줄 수: {schedules.count()}")
    
    for schedule in schedules:
        min_price = schedule.minimum_price if schedule.minimum_price else 0
        status = get_status_text(schedule.result_status)
        schedule_display = schedule.schedule_type or f"{schedule.round_number}차"
        
        bidding_history.append({
            'id': schedule.round_number,
            'link_text': f"{case.case_number} {schedule_display}",
            'type': schedule_display,
            'min_price': f"{min_price:,}" if min_price > 0 else "정보없음",
            'status': status,
            'auction_date': schedule.auction_date,
            'due_date': schedule.decision_date
        })
        
        print(f"📊 입찰 내역 추가 - 회차: {schedule.round_number}, 가격: {min_price}, 상태: {status}")
    
    return bidding_history

def get_valuation_amount(item_details):
    """감정평가액 추출 및 정수 변환"""
    
    valuation_amount = 0
    if item_details and item_details.valuation_amount:
        try:
            if isinstance(item_details.valuation_amount, str):
                # 문자열에서 숫자만 추출
                val_str = ''.join(c for c in item_details.valuation_amount if c.isdigit())
                valuation_amount = int(val_str) if val_str else 0
            else:
                valuation_amount = int(item_details.valuation_amount)
        except (ValueError, TypeError):
            valuation_amount = 0
    
    return valuation_amount

def get_building_details(item_details):
    """건물 상세정보 가져오기"""
    
    building_details = []
    if item_details:
        try:
            building_details_qs = BuildingDetail.objects.filter(
                auction_item=item_details
            ).order_by('sequence')
            building_details = list(building_details_qs)
        except Exception as e:
            print(f"❌ BuildingDetail 조회 오류: {e}")
    
    return building_details