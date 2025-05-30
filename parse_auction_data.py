import json
import os
import django
from datetime import datetime
from django.utils.dateparse import parse_date, parse_datetime

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')  # 프로젝트명에 맞게 수정
django.setup()

from app.models import AuctionCase, ClaimDistribution, AuctionItem, PropertyListing, AuctionParty, AuctionSchedule

def clean_image_data(data):
    """이미지 관련 데이터를 제거하는 함수"""
    if isinstance(data, dict):
        keys_to_remove = []
        for key in data.keys():
            if any(keyword in key.lower() for keyword in ['picfile', 'image', 'img', 'photo', 'picture', 'pic']):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del data[key]
        
        for key, value in data.items():
            data[key] = clean_image_data(value)
    
    elif isinstance(data, list):
        for i, item in enumerate(data):
            data[i] = clean_image_data(item)
    
    return data

def safe_date_parse(date_str):
    """안전한 날짜 파싱"""
    if not date_str:
        return None
    
    try:
        if isinstance(date_str, str) and len(date_str) == 8 and date_str.isdigit():
            return datetime.strptime(date_str, '%Y%m%d').date()
        
        parsed = parse_date(date_str)
        if parsed:
            return parsed
            
        parsed = parse_datetime(date_str)
        if parsed:
            return parsed.date()
            
    except:
        pass
    
    return None

def safe_datetime_parse(date_str, time_str=None):
    """안전한 날짜시간 파싱"""
    if not date_str:
        return None
    
    try:
        if isinstance(date_str, str) and len(date_str) == 8 and date_str.isdigit():
            if time_str and len(time_str) == 4 and time_str.isdigit():
                combined = f"{date_str} {time_str[:2]}:{time_str[2:]}"
                return datetime.strptime(combined, '%Y%m%d %H:%M')
            else:
                return datetime.strptime(date_str, '%Y%m%d')
        
        parsed = parse_datetime(date_str)
        if parsed:
            return parsed
            
    except:
        pass
    
    return None

def get_schedule_type(kind_code):
    """매각기일 종류 코드를 텍스트로 변환"""
    kind_mapping = {
        '01': '매각기일',
        '02': '매각결정기일',
        '03': '대금지급기한'
    }
    return kind_mapping.get(kind_code, '기타')

def parse_auction_data(json_file_path):
    """JSON 파일을 파싱하여 데이터베이스에 저장"""
    
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 이미지 데이터 제거
    data = clean_image_data(data)
    
    if 'data' not in data or 'dma_result' not in data['data']:
        print("Invalid data structure")
        return
    
    dma_result = data['data']['dma_result']
    
    # 1. AuctionCase 생성
    case_info = dma_result.get('csBaseInfo', {})
    case_number = case_info.get('userCsNo') or case_info.get('csNo')
    
    if not case_number:
        print("Case number not found")
        return
    
    auction_case, created = AuctionCase.objects.get_or_create(
        case_number=case_number,
        defaults={
            'case_name': case_info.get('csNm'),
            'court_name': case_info.get('cortOfcNm'),
            'filing_date': safe_date_parse(case_info.get('csRcptYmd')),
            'responsible_dept': case_info.get('cortAuctnJdbnNm'),
            'claim_amount': str(case_info.get('clmAmt', '')),
            'appeal_status': case_info.get('rletApalYn') == 'Y',
            'minimum_bid_price': ''
        }
    )
    
    if created:
        print(f"Created new auction case: {case_number}")
    else:
        print(f"Auction case already exists: {case_number}")
    
    # 2. ClaimDistribution 생성
    distrt_info = dma_result.get('dstrtDemnInfo', [])
    if distrt_info:
        # 소재지 정보를 객체 정보에서 가져오기
        location = ""
        objects_info = dma_result.get('gdsDspslObjctLst', [])
        if objects_info:
            obj_info = objects_info[0]
            location = f"{obj_info.get('adongSdNm', '')} {obj_info.get('adongSggNm', '')} {obj_info.get('adongEmdNm', '')} {obj_info.get('rprsLtnoAddr', '')}"
        
        for dist in distrt_info:
            claim_dist, created = ClaimDistribution.objects.get_or_create(
                case_number=auction_case,
                defaults={
                    'location': location.strip(),
                    'claim_deadline': safe_date_parse(dist.get('dstrtDemnLstprdYmd'))
                }
            )
            if created:
                print(f"Created claim distribution for case: {case_number}")
    
    # 3. AuctionItem 생성
    item_info = dma_result.get('dspslGdsDxdyInfo', {})
    objects_info = dma_result.get('gdsDspslObjctLst', [])

    # 매물명 추출 (건물명)
    property_name = ""
    if objects_info:
        obj_info = objects_info[0]
        property_name = obj_info.get('bldNm', '')  # 건물명

    if item_info:
        auction_item, created = AuctionItem.objects.get_or_create(
            item_number=item_info.get('dspslGdsSeq', 1),
            case_number=auction_case,
            defaults={
                'property_name': property_name,  # 새로 추가
                'valuation_amount': str(item_info.get('aeeEvlAmt', '')),
                'auction_failures': item_info.get('flbdNcnt', 0),
                'auction_date': safe_datetime_parse(
                    item_info.get('dspslDxdyYmd'), 
                    item_info.get('fstDspslHm')
                ),
                'item_status': item_info.get('auctnGdsStatCd'),
            }
        )
        
        if created:
            print(f"✓ Created auction item: {property_name} ({item_info.get('dspslGdsSeq', 1)})")
        
        # 4. AuctionSchedule 생성 (매각기일 정보)
        schedules = dma_result.get('gdsDspslDxdyLst', [])
        for idx, schedule in enumerate(schedules, 1):
            auction_date = None
            decision_date = None
            
            kind_code = schedule.get('auctnDxdyKndCd')
            schedule_type = get_schedule_type(kind_code)
            
            if kind_code == '01':  # 매각기일
                auction_date = safe_datetime_parse(
                    schedule.get('dxdyYmd'), 
                    schedule.get('dxdyHm')
                )
            elif kind_code == '02':  # 매각결정기일
                decision_date = safe_datetime_parse(
                    schedule.get('dxdyYmd'), 
                    schedule.get('dxdyHm')
                )
            elif kind_code == '03':  # 대금지급기한
                decision_date = safe_datetime_parse(
                    schedule.get('dxdyYmd'), 
                    schedule.get('dxdyHm')
                )
            
            # tsLwsDspslPrc 값 사용 (실제 최저매각가격)
            minimum_price = schedule.get('tsLwsDspslPrc', 0)
            
            auction_schedule, created = AuctionSchedule.objects.get_or_create(
                auction_item=auction_item,
                round_number=idx,
                defaults={
                    'auction_date': auction_date,
                    'decision_date': decision_date,
                    'minimum_price': minimum_price,  # tsLwsDspslPrc 값 저장
                    'result_status': schedule.get('auctnDxdyRsltCd'),
                    'schedule_type': schedule_type
                }
            )
            
            if created:
                print(f"✓ Created auction schedule round {idx} ({schedule_type}) - Price: {minimum_price:,} for item {auction_item.item_number}")
    
    # 5. PropertyListing 생성
    objects_info = dma_result.get('gdsDspslObjctLst', [])
    for obj_info in objects_info:
        location = f"{obj_info.get('adongSdNm', '')} {obj_info.get('adongSggNm', '')} {obj_info.get('adongEmdNm', '')} {obj_info.get('rprsLtnoAddr', '')}"
        
        property_listing, created = PropertyListing.objects.get_or_create(
            case_number=auction_case,
            location=location.strip(),
            defaults={
                'listing_type': obj_info.get('rletDvsDts'),
                'details': obj_info.get('pjbBuldList')
            }
        )
        
        if created:
            print(f"Created property listing for case: {case_number}")
    
    print(f"Successfully parsed auction case: {case_number}")

if __name__ == "__main__":
    # 사용 예시
    parse_auction_data('data.json')