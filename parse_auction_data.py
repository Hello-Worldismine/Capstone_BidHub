import json
import os
import django
from datetime import datetime
from django.utils.dateparse import parse_date, parse_datetime
import re

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')  # 프로젝트명에 맞게 수정
django.setup()

from app.models import AuctionCase, ClaimDistribution, AuctionItem, PropertyListing, AuctionParty, AuctionSchedule, PropertyDocument

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

def extract_building_name(rdnm_addr):
    """도로명주소에서 건물명을 추출하는 함수"""
    if not rdnm_addr:
        return ""
    
    # 괄호 안의 건물명 추출 (예: "서울특별시 관악구 신림로 330 (신림동, 신림큐브)")
    pattern = r'\([^,]+,\s*([^)]+)\)'
    match = re.search(pattern, rdnm_addr)
    if match:
        return match.group(1).strip()
    
    # 괄호 안에 쉼표가 없는 경우 (예: "서울특별시 관악구 신림로 330 (신림큐브)")
    pattern = r'\(([^)]+)\)'
    match = re.search(pattern, rdnm_addr)
    if match:
        building_name = match.group(1).strip()
        # 동 이름이 아닌 경우만 반환 (동으로 끝나지 않는 경우)
        if not building_name.endswith('동'):
            return building_name
    
    return ""

def extract_area_info(area_str):
    """면적 정보를 추출하여 평수와 함께 포맷팅하는 함수"""
    if not area_str:
        return ""
    
    try:
        # 숫자와 소수점만 추출
        area_match = re.search(r'(\d+\.?\d*)', str(area_str))
        if area_match:
            area_sqm = float(area_match.group(1))
            # 평수 계산 (1평 = 3.3058㎡)
            area_pyeong = area_sqm / 3.3058
            return f"{area_sqm:.2f}㎡ ({area_pyeong:.0f}평)"
    except:
        pass
    
    return str(area_str)

def extract_area_from_bld_details(bld_details):
    """건물 상세정보에서 면적을 추출하는 함수"""
    if not bld_details:
        return ""
    
    print(f"🔍 건물상세정보 분석: {bld_details}")
    
    # 1. 단순한 면적 패턴 (예: "철근콘크리트구조 24.18㎡")
    simple_pattern = r'(\d+\.?\d*)\s*㎡'
    matches = re.findall(simple_pattern, bld_details)
    
    if matches:
        # 마지막 면적이 가장 관련성이 높을 가능성
        last_area = matches[-1]
        print(f"🏠 발견된 면적: {last_area}㎡")
        return extract_area_info(last_area)
    
    # 2. 층별 면적이 나열된 경우, 총 면적 계산
    floor_pattern = r'(\d+\.?\d*)\s*㎡'
    all_areas = re.findall(floor_pattern, bld_details)
    
    if len(all_areas) > 1:
        try:
            total_area = sum(float(area) for area in all_areas)
            area_pyeong = total_area / 3.3058
            print(f"🏠 총 면적 계산: {total_area:.2f}㎡")
            return f"{total_area:.2f}㎡ ({area_pyeong:.0f}평) [총합]"
        except:
            pass
    
    return ""

def extract_land_and_building_area(objects_info, rglt_land_lst, bld_sdtr_dtl_lst):
    """토지면적과 건물면적을 추출하는 함수"""
    land_area = ""
    building_area = ""
    
    print("🔍 면적 정보 추출 시작...")
    
    # 1. 토지면적 추출
    if rglt_land_lst:
        print(f"📊 토지 정보 개수: {len(rglt_land_lst)}")
        for i, land_info in enumerate(rglt_land_lst):
            if isinstance(land_info, dict):
                print(f"📊 토지정보 {i+1}: {land_info.keys()}")
                # 대지권면적 또는 토지면적 필드들 확인
                land_fields = ['siteRghtAr', 'lndAr', 'totar', 'landArea']
                for field in land_fields:
                    if land_info.get(field):
                        land_area = extract_area_info(land_info.get(field))
                        print(f"🏞️  토지면적 발견 ({field}): {land_area}")
                        break
                if land_area:
                    break
    
    # objects_info에서도 토지면적 확인
    if not land_area and objects_info:
        print("📊 객체정보에서 토지면적 검색...")
        for obj_info in objects_info:
            land_fields = ['siteRghtAr', 'lndAr', 'landArea']
            for field in land_fields:
                if obj_info.get(field):
                    land_area = extract_area_info(obj_info.get(field))
                    print(f"🏞️  토지면적 발견 (객체-{field}): {land_area}")
                    break
            if land_area:
                break
    
    # 2. 건물면적 추출 (개선된 부분)
    if bld_sdtr_dtl_lst:
        print(f"🏠 건물 정보 개수: {len(bld_sdtr_dtl_lst)}")
        for i, bld_info in enumerate(bld_sdtr_dtl_lst):
            if isinstance(bld_info, dict):
                print(f"🏠 건물정보 {i+1}: {bld_info.keys()}")
                
                # 1) bldSdtrDtlDts에서 면적 추출 (새로 추가)
                bld_details = bld_info.get('bldSdtrDtlDts')
                if bld_details:
                    extracted_area = extract_area_from_bld_details(bld_details)
                    if extracted_area:
                        building_area = extracted_area
                        print(f"🏠 건물면적 발견 (상세정보): {building_area}")
                        break
                
                # 2) 기존 필드들에서 건물면적 확인
                building_fields = ['bldTotar', 'flrAr', 'bldAr', 'buildingArea']
                for field in building_fields:
                    if bld_info.get(field):
                        building_area = extract_area_info(bld_info.get(field))
                        print(f"🏠 건물면적 발견 ({field}): {building_area}")
                        break
                
                if building_area:
                    break
    
    # objects_info에서도 건물면적 확인
    if not building_area and objects_info:
        print("🏠 객체정보에서 건물면적 검색...")
        for obj_info in objects_info:
            building_fields = ['bldTotar', 'flrAr', 'bldAr', 'buildingArea']
            for field in building_fields:
                if obj_info.get(field):
                    building_area = extract_area_info(obj_info.get(field))
                    print(f"🏠 건물면적 발견 (객체-{field}): {building_area}")
                    break
            if building_area:
                break
    
    if not land_area:
        print("⚠️  토지면적을 찾을 수 없습니다.")
    if not building_area:
        print("⚠️  건물면적을 찾을 수 없습니다.")
    
    return land_area, building_area

def extract_property_type(dspsl_gds_info, objects_info, bld_sdtr_dtl_lst):
    """물건 상세 정보에서 부동산 종류를 추출하는 함수"""
    property_type = "기타"
    
    # 부동산 종류 키워드 매핑
    property_types = {
        '오피스텔': ['오피스텔', 'officetel', '업무시설'],
        '아파트': ['아파트', 'apartment', '공동주택', '아파트형'],
        '상가': ['상가', '점포', '상업시설', '매장', '상업용', '근린생활시설'],
        '사무실': ['사무실', '사무소', 'office', '업무용'],
        '빌딩': ['빌딩', '상업빌딩', 'building'],
        '주택': ['주택', '단독주택', '연립주택', '다세대주택', '다가구주택'],
        '토지': ['토지', '대지', '임야', '전', '답', '잡종지'],
        '창고': ['창고', '물류창고', 'warehouse', '창고시설'],
        '공장': ['공장', '제조시설', 'factory', '산업시설'],
        '펜션': ['펜션', '리조트', '숙박시설', '관광시설']
    }
    
    print("🔍 부동산 종류 분석 시작...")
    
    # 1. dspslGdsDxdyInfo의 auctnGdsUsgCd 확인
    if dspsl_gds_info:
        usage_code = dspsl_gds_info.get('auctnGdsUsgCd')
        print(f"📋 용도코드: {usage_code}")
        if usage_code:
            # 경매 물건 용도 코드 매핑 (오피스텔 추가)
            usage_code_mapping = {
                '01': '토지',
                '02': '주택',
                '03': '아파트',
                '04': '연립주택',
                '05': '다세대주택',
                '06': '오피스텔',
                '07': '상가',
                '08': '사무실',
                '09': '공장',
                '10': '창고',
                '17': '오피스텔',  # data.json의 경우 (17번이 오피스텔)
            }
            if usage_code in usage_code_mapping:
                property_type = usage_code_mapping[usage_code]
                print(f"🏷️  용도코드 {usage_code}로 부동산 종류 결정: {property_type}")
                return property_type
    
    # 2. 건물 세부정보에서 확인 (bldSdtrDtlDts 추가)
    if bld_sdtr_dtl_lst:
        print("🏠 건물 세부정보에서 용도 확인...")
        for bld_info in bld_sdtr_dtl_lst:
            if isinstance(bld_info, dict):
                # bldSdtrDtlDts에서 용도 확인 (새로 추가)
                bld_details = bld_info.get('bldSdtrDtlDts', '')
                print(f"🔍 건물상세: {bld_details}")
                if bld_details:
                    bld_details_lower = bld_details.lower()
                    for prop_type, keywords in property_types.items():
                        if any(keyword in bld_details_lower for keyword in keywords):
                            property_type = prop_type
                            print(f"🏷️  건물상세정보에서 '{bld_details[:50]}...'로 부동산 종류 결정: {property_type}")
                            return property_type
                
                # 기존 필드들도 확인
                text_fields = ['mainPrpsNm', 'dtlPrpsNm', 'bldUsage']
                for field in text_fields:
                    field_value = bld_info.get(field, '')
                    if field_value:
                        field_lower = str(field_value).lower()
                        for prop_type, keywords in property_types.items():
                            if any(keyword in field_lower for keyword in keywords):
                                property_type = prop_type
                                print(f"🏷️  건물정보 {field}에서 '{field_value}'로 부동산 종류 결정: {property_type}")
                                return property_type
    
    # 3. objects_info에서 용도 정보 확인
    if objects_info:
        print("📍 객체정보에서 용도 확인...")
        for obj_info in objects_info:
            # 건물 상세 정보에서 키워드 검색
            text_fields = ['pjbBuldList', 'bldUsageMainCd', 'bldMainPrpsNm', 'mainPrpsNm', 'rletDvsDts']
            for field in text_fields:
                field_value = obj_info.get(field, '')
                if field_value:
                    print(f"📋 {field}: {field_value}")
                    field_lower = str(field_value).lower()
                    for prop_type, keywords in property_types.items():
                        if any(keyword in field_lower for keyword in keywords):
                            property_type = prop_type
                            print(f"🏷️  {field}에서 '{field_value}'로 부동산 종류 결정: {property_type}")
                            return property_type
    
    print(f"🏷️  부동산 종류를 결정할 수 없어 기본값 사용: {property_type}")
    return property_type

def extract_property_name(objects_info, dspsl_gds_info):
    """매물명을 추출하는 개선된 함수"""
    property_name = ""
    
    print("🔍 매물명 추출 시작...")
    
    # 1. objects_info에서 건물명 추출 시도
    if objects_info:
        obj_info = objects_info[0]
        print(f"📍 객체 정보: {list(obj_info.keys())}")
        
        # 다양한 필드에서 건물명 추출 시도
        name_fields = ['bldNm', 'bldName', 'propertyName', 'buildingName']
        for field in name_fields:
            if obj_info.get(field):
                property_name = obj_info.get(field)
                print(f"🏢 {field}에서 건물명 발견: '{property_name}'")
                break
        
        # 도로명주소에서 건물명 추Extract
        if not property_name:
            rdnm_fields = ['rdnmRefcAddr', 'rdnmAddr', 'roadNameAddr']
            for field in rdnm_fields:
                rdnm_addr = obj_info.get(field, '')
                if rdnm_addr:
                    extracted_name = extract_building_name(rdnm_addr)
                    if extracted_name:
                        property_name = extracted_name
                        print(f"🏢 {field}에서 건물명 추출: '{property_name}' (from: {rdnm_addr})")
                        break
        
        # 여전히 건물명이 없으면 기타 필드들 확인
        if not property_name:
            other_fields = ['pjbBuldList', 'bldDetails', 'description']
            for field in other_fields:
                field_value = obj_info.get(field, '')
                if field_value and len(str(field_value)) < 100:  # 너무 긴 설명은 제외
                    property_name = str(field_value).strip()
                    print(f"🏢 {field}에서 설명 추출: '{property_name}'")
                    break
    
    # 2. dspsl_gds_info에서 추출 시도
    if not property_name and dspsl_gds_info:
        print("📋 물건정보에서 매물명 검색...")
        name_fields = ['gdsSpcfcRmk', 'dspslGdsRmk', 'propertyName']
        for field in name_fields:
            field_value = dspsl_gds_info.get(field, '')
            if field_value:
                # 긴 설명에서 건물명 추출 시도
                lines = str(field_value).split('\n')
                for line in lines:
                    if len(line.strip()) < 50 and '건물' in line:
                        property_name = line.strip()
                        print(f"🏢 {field}에서 건물명 추출: '{property_name}'")
                        break
                if property_name:
                    break
    
    # 3. 최종적으로 기본값 설정
    if not property_name:
        property_name = "매물정보"
        print(f"⚠️  매물명을 찾을 수 없어 기본값 사용: '{property_name}'")
    
    return property_name

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

def extract_building_details(objects_info, rglt_land_lst, bld_sdtr_dtl_lst, gds_rlet_st_lst):
    """목록내역 정보를 추출하는 함수"""
    building_details = []
    
    print("🔍 목록내역 추출 시작...")
    
    if not objects_info:
        return building_details
    
    for obj_idx, obj_info in enumerate(objects_info, 1):
        # 기본 정보 수집
        address = f"{obj_info.get('adongSdNm', '')} {obj_info.get('adongSggNm', '')} {obj_info.get('adongEmdNm', '')} {obj_info.get('rprsLtnoAddr', '')}"
        building_name = obj_info.get('bldNm', '')
        road_address = f"{obj_info.get('rdnmSdNm', '')} {obj_info.get('rdnmSggNm', '')} {obj_info.get('rdnm', '')} {obj_info.get('rdnmBldNo', '')}"
        building_detail = obj_info.get('bldDtlDts', '')  # 2층204호
        
        # 상세내역 구성
        detail_parts = []
        
        # 1동의 건물의 표시
        detail_parts.append("1동의 건물의 표시")
        detail_parts.append(address.strip())
        if building_name:
            detail_parts.append(building_name)
        detail_parts.append("[도로명주소]")
        detail_parts.append(road_address.strip())
        
        # 건물 구조 정보 (bldSdtrDtlLstAll에서)
        if bld_sdtr_dtl_lst:
            for bld_info in bld_sdtr_dtl_lst:
                if bld_info.get('rletDvsDts') == '1동':
                    bld_details = bld_info.get('bldSdtrDtlDts', '')
                    if bld_details:
                        # 층별 정보를 개행으로 분리
                        lines = bld_details.split('\n')
                        for line in lines:
                            if line.strip():
                                detail_parts.append(line.strip())
        
        # 전유부분의 건물의 표시
        detail_parts.append("전유부분의 건물의 표시")
        if building_detail:
            detail_parts.append(f"건물의 번호 : {building_detail}")
        
        # 전유부분 구조 정보
        if bld_sdtr_dtl_lst:
            for bld_info in bld_sdtr_dtl_lst:
                if bld_info.get('rletDvsDts') == '전유':
                    exclusive_details = bld_info.get('bldSdtrDtlDts', '')
                    if exclusive_details:
                        detail_parts.append(f"구조 : {exclusive_details}")
        
        # 대지권의 목적인 토지의 표시
        if rglt_land_lst:
            detail_parts.append("대지권의 목적인 토지의 표시")
            for land_idx, land_info in enumerate(rglt_land_lst, 1):
                land_address = land_info.get('rletIndctDts', '')
                land_area = land_info.get('landArDts', '')
                land_type = land_info.get('landLdcgDts', '')
                
                if land_address:
                    detail_parts.append(f"토지의 표시 : {land_idx}. {land_address}")
                if land_area and land_type:
                    detail_parts.append(f"{land_type} {land_area}")
                
                # 대지권 정보
                rglt_rate_dnmn = land_info.get('rgltRateDnmnVal', '')
                rglt_rate_nmrt = land_info.get('rgltRateNmrtVal', '')
                if rglt_rate_dnmn and rglt_rate_nmrt:
                    detail_parts.append(f"대지권의 종류 : {land_idx}. 소유권")
                    detail_parts.append(f"대지권의 비율 : {land_idx}. {rglt_rate_dnmn} 분의 {rglt_rate_nmrt}")
        
        # 목록구분 결정
        listing_type = "집합건물"  # 기본값
        if obj_info.get('rletDvsDts') == '전유':
            listing_type = "집합건물"
        
        building_detail_obj = {
            'sequence': obj_idx,
            'address': address.strip(),
            'building_type': listing_type,
            'building_details': '\n'.join(detail_parts)
        }
        
        building_details.append(building_detail_obj)
        print(f"✓ 목록내역 {obj_idx} 생성완료")
    
    return building_details

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
    rglt_land_lst = dma_result.get('rgltLandLstAll', [[]])[0] if dma_result.get('rgltLandLstAll') else []
    bld_sdtr_dtl_lst = dma_result.get('bldSdtrDtlLstAll', [[]])[0] if dma_result.get('bldSdtrDtlLstAll') else []
    gds_rlet_st_lst = dma_result.get('gdsRletStLtnoLstAll', [[]])[0] if dma_result.get('gdsRletStLtnoLstAll') else []

    # 매물명 추출 (개선된 함수 사용)
    property_name = extract_property_name(objects_info, item_info)
    
    # 토지면적과 건물면적 추출
    land_area, building_area = extract_land_and_building_area(objects_info, rglt_land_lst, bld_sdtr_dtl_lst)
    
    # 부동산 종류 추출
    property_type = extract_property_type(item_info, objects_info, bld_sdtr_dtl_lst)
    
    # 목록내역 추출 (새로 추가)
    building_details = extract_building_details(objects_info, rglt_land_lst, bld_sdtr_dtl_lst, gds_rlet_st_lst)
    
    print(f"🏢 최종 매물명: '{property_name}'")
    print(f"🏞️  토지면적: '{land_area}'")
    print(f"🏠 건물면적: '{building_area}'")
    print(f"🏷️  부동산 종류: '{property_type}'")
    print(f"📋 목록내역 개수: {len(building_details)}")

    if item_info:
        # 주소 정보 추출 및 초기화
        prop_addr_final = ""
        prop_detail_addr_final = ""

        if objects_info:
            main_obj_info = objects_info[0]  # 일반적으로 첫 번째 객체 정보를 사용
            
            # 도로명 주소 구성 (예: "서울특별시 강남구 테헤란로 123")
            road_address_parts = [
                main_obj_info.get('rdnmSdNm', ''),
                main_obj_info.get('rdnmSggNm', ''),
                main_obj_info.get('rdnm', ''),
                main_obj_info.get('rdnmBldNo', '')
            ]
            prop_addr_final = " ".join(filter(None, road_address_parts)).strip()
            
            # 상세 주소 (예: "2층204호", "101동 505호")
            # main_obj_info.get('bldDtlDts')가 None을 반환할 경우를 대비하여 or '' 추가
            prop_detail_addr_final = (main_obj_info.get('bldDtlDts') or '').strip()
        else:
            # objects_info가 없을 경우, item_info의 dspslGdsAddr 사용
            # 이 경우, dspslGdsAddr 전체를 property_address에 할당하고, 
            # property_detail_address는 비워두거나, 별도 파싱 로직 필요.
            # extract_building_name 함수는 건물명 추출용이므로 여기서는 직접 사용하지 않음.
            full_address_from_item_info = item_info.get('dspslGdsAddr', '')
            prop_addr_final = full_address_from_item_info
            prop_detail_addr_final = "" # 상세 주소 파싱 로직이 없다면 비워둠

        auction_item_defaults = {
            'property_name': property_name,
            'valuation_amount': str(item_info.get('aeeEvlAmt', '')),
            'auction_failures': item_info.get('flbdNcnt', 0),
            'auction_date': safe_datetime_parse(
                item_info.get('dspslDxdyYmd'), 
                item_info.get('fstDspslHm')
            ),
            'item_status': item_info.get('auctnGdsStatCd'),
            'building_area': building_area,
            'property_type': property_type,
            'property_address': prop_addr_final,  # 도로명 주소
            'property_detail_address': prop_detail_addr_final,  # 상세 주소
        }

        auction_item, created = AuctionItem.objects.get_or_create(
            item_number=item_info.get('dspslGdsSeq', 1),
            case_number=auction_case,
            defaults=auction_item_defaults
        )
        
        if created:
            print(f"✓ Created auction item: {property_name} ({item_info.get('dspslGdsSeq', 1)}) with address: '{prop_addr_final}', '{prop_detail_addr_final}'")
        else:
            # 기존 항목이 있으면 정보 업데이트
            update_fields = False
            for field, value in auction_item_defaults.items():
                if getattr(auction_item, field) != value:
                    setattr(auction_item, field, value)
                    update_fields = True
            
            if update_fields:
                auction_item.save()
                print(f"✓ Updated auction item: {property_name} ({auction_item.item_number}) with new data including address: '{prop_addr_final}', '{prop_detail_addr_final}'")
            else:
                print(f"✓ Auction item: {property_name} ({auction_item.item_number}) data is already up to date.")
        
        # 6. BuildingDetail 생성 (새로 추가)
        if building_details:
            from app.models import BuildingDetail  # import 추가
            
            # 기존 건물 상세정보 삭제 (업데이트를 위해)
            BuildingDetail.objects.filter(auction_item=auction_item).delete()
            
            for detail in building_details:
                BuildingDetail.objects.create(
                    auction_item=auction_item,
                    sequence=detail['sequence'],
                    address=detail['address'],
                    building_type=detail['building_type'],
                    building_details=detail['building_details']
                )
                print(f"✓ Created building detail {detail['sequence']}")
        
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
                    'minimum_price': minimum_price,
                    'result_status': schedule.get('auctnDxdyRsltCd'),
                    'schedule_type': schedule_type
                }
            )
            
            if created:
                price_display = f"{minimum_price:,}" if minimum_price is not None else "N/A"
                item_number = getattr(auction_item, 'item_number', 'Unknown')
                print(f"✓ Created auction schedule round {idx} ({schedule_type}) - Price: {price_display} for item {item_number}")
    
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
    
    # 6. 매각물건명세서 URL 입력받기
    print("\n" + "="*50)
    print("📋 매각물건명세서 URL 입력")
    print("="*50)
    print(f"사건번호: {case_number}")
    if 'auction_item' in locals():
        print(f"물건번호: {auction_item.item_number}")
        print(f"매물명: {property_name or '정보없음'}")
    print("💡 법원 사이트에서 매각물건명세서 URL을 복사해서 붙여넣으세요")
    print("❌ 건너뛰려면 그냥 엔터를 누르세요")
    print("-"*50)
    
    spec_url = input("매각물건명세서 URL: ").strip()
    
    if spec_url:
        # PropertyDocument 생성 또는 업데이트
        if 'auction_item' in locals():
            property_doc, doc_created = PropertyDocument.objects.get_or_create(
                auction_item=auction_item,
                defaults={'specification_url': spec_url}
            )
            
            if not doc_created:
                # 이미 존재하면 URL 업데이트
                property_doc.specification_url = spec_url
                property_doc.save()
            
            print("✅ 매각물건명세서 URL이 저장되었습니다!")
        else:
            print("⚠️  물건 정보가 없어서 URL을 저장할 수 없습니다.")
    else:
        print("⏭️  매각물건명세서 URL 입력을 건너뛰었습니다.")

if __name__ == "__main__":
    # 사용 예시
    json_file_to_parse = 'data.json'
    parse_auction_data(json_file_to_parse)

    # parse_auction_data 실행 후 data.json 파일 비우기
    try:
        with open(json_file_to_parse, 'w', encoding='utf-8') as f:
            json.dump({}, f) # 빈 JSON 객체로 초기화
        print(f"\n✓ '{json_file_to_parse}' 파일의 내용이 비워졌습니다.")
    except Exception as e:
        print(f"\n⚠️ '{json_file_to_parse}' 파일 비우기 실패: {e}")