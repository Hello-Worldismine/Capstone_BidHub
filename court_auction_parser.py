import requests
import json
from datetime import datetime, date
from typing import Dict, List, Optional, Any
import logging
import os
import django

# Django 설정 로드
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from app.models import AuctionCase, AuctionItem

class CourtAuctionParser:
    def __init__(self):
        self.base_url = "https://www.courtauction.go.kr/pgj/pgj15B/selectAuctnCsSrchRslt.on"
        self.headers = {
            'Accept': 'application/json',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
            'Content-Type': 'application/json;charset=UTF-8',
            'Host': 'www.courtauction.go.kr',
            'Origin': 'https://www.courtauction.go.kr',
            'Referer': 'https://www.courtauction.go.kr/pgj/index.on?w2xPath=/pgj/ui/pgj100/PGJ151F00.xml',
            'Sc-Pgmid': 'PGJ15BM01',
            'Sc-Userid': 'NONUSER',
            'Sec-Ch-Ua': '"Chromium";v="136", "Google Chrome";v="136", "Not.A/Brand";v="99"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin',
            'Submissionid': 'mf_wfm_mainFrame_sbm_selectGdsDtlSrchDtlInfo',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36'
        }
        
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def create_payload(self, case_number: str, court_code: str = "B000210", item_seq: str = "1") -> Dict[str, Any]:
        """API 요청을 위한 페이로드 생성"""
        today = datetime.now().strftime("%Y%m%d")
        end_date = "20250608"
        
        payload = {
            "dma_srchGdsDtlSrch": {
                "csNo": case_number,
                "cortOfcCd": court_code,
                "dspslGdsSeq": item_seq,
                "pgmId": "PGJ151F01",
                "srchInfo": {
                    "rletDspslSpcCondCd": "",
                    "bidDvsCd": "",
                    "mvprpRletDvsCd": "00031R",
                    "cortAuctnSrchCondCd": "0004601",
                    "rprsAdongSdCd": "",
                    "rprsAdongSggCd": "",
                    "rprsAdongEmdCd": "",
                    "rdnmSdCd": "",
                    "rdnmSggCd": "",
                    "rdnmNo": "",
                    "mvprpDspslPlcAdongSdCd": "",
                    "mvprpDspslPlcAdongSggCd": "",
                    "mvprpDspslPlcAdongEmdCd": "",
                    "rdDspslPlcAdongSdCd": "",
                    "rdDspslPlcAdongSggCd": "",
                    "rdDspslPlcAdongEmdCd": "",
                    "cortOfcCd": court_code,
                    "jdbnCd": "1004",
                    "execrOfcDvsCd": "",
                    "lclDspslGdsLstUsgCd": "",
                    "mclDspslGdsLstUsgCd": "",
                    "sclDspslGdsLstUsgCd": "",
                    "cortAuctnMbrsId": "",
                    "aeeEvlAmtMin": "",
                    "aeeEvlAmtMax": "",
                    "lwsDspslPrcRateMin": "",
                    "lwsDspslPrcRateMax": "",
                    "flbdNcntMin": "",
                    "flbdNcntMax": "",
                    "objctArDtsMin": "",
                    "objctArDtsMax": "",
                    "mvprpArtclKndCd": "",
                    "mvprpArtclNm": "",
                    "mvprpAtchmPlcTypCd": "",
                    "notifyLoc": "off",
                    "lafjOrderBy": "",
                    "pgmId": "PGJ151F01",
                    "csNo": "",
                    "cortStDvs": "1",
                    "statNum": 1,
                    "bidBgngYmd": today,
                    "bidEndYmd": end_date,
                    "dspslDxdyYmd": "",
                    "fstDspslHm": "",
                    "scndDspslHm": "",
                    "thrdDspslHm": "",
                    "fothDspslHm": "",
                    "dspslPlcNm": "",
                    "lwsDspslPrcMin": "",
                    "lwsDspslPrcMax": "",
                    "grbxTypCd": "",
                    "gdsVendNm": "",
                    "fuelKndCd": "",
                    "carMdyrMax": "",
                    "carMdyrMin": "",
                    "carMdlNm": "",
                    "sideDvsCd": "2",
                    "menuNm": "물건상세검색"
                }
            }
        }
        return payload
    
    def fetch_auction_data(self, case_number: str, court_code: str = "B000210") -> Optional[Dict[str, Any]]:
        """법원 경매 API에서 데이터 가져오기"""
        try:
            payload = self.create_payload(case_number, court_code)
            
            response = requests.post(
                self.base_url,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                self.logger.error(f"API 요청 실패: {response.status_code}")
                return None
                
        except requests.RequestException as e:
            self.logger.error(f"API 요청 중 오류 발생: {str(e)}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"JSON 디코딩 오류: {str(e)}")
            return None
    
    def parse_and_save_auction_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """API 응답을 파싱하여 Django 모델에 저장"""
        try:
            if raw_data.get('status') != 200:
                self.logger.error(f"API 오류: {raw_data.get('message', 'Unknown error')}")
                return None
            
            dma_result = raw_data.get('data', {}).get('dma_result', {})
            
            # 1. AuctionCase 생성/업데이트
            case_info = self.parse_auction_case(dma_result)
            auction_case = self.save_auction_case(case_info)
            
            # 2. AuctionItem 생성/업데이트
            item_info = self.parse_auction_item(dma_result, auction_case)
            auction_item = self.save_auction_item(item_info)
            
            return {
                'case': auction_case,
                'item': auction_item,
                'raw_data': raw_data
            }
            
        except Exception as e:
            self.logger.error(f"데이터 파싱/저장 중 오류: {str(e)}")
            return None
    
    def parse_auction_case(self, dma_result: Dict[str, Any]) -> Dict[str, Any]:
        """AuctionCase 모델에 맞는 데이터 파싱"""
        cs_base_info = dma_result.get('csBaseInfo', {})
        
        return {
            'case_number': cs_base_info.get('userCsNo', ''),  # 2022타경113322 형식
            'case_name': cs_base_info.get('csNm', ''),
            'court_name': cs_base_info.get('cortOfcNm', ''),
            'filing_date': self.parse_date(cs_base_info.get('csRcptYmd', '')),
            'responsible_dept': cs_base_info.get('cortAuctnJdbnNm', ''),
            'claim_amount': str(cs_base_info.get('clmAmt', 0)),
            'appeal_status': cs_base_info.get('rletApalYn', 'N') == 'Y',
            'minimum_bid_price': str(cs_base_info.get('clmAmt', 0)),  # 청구금액을 최저가로 임시 설정
        }
    
    def parse_auction_item(self, dma_result: Dict[str, Any], auction_case) -> Dict[str, Any]:
        """AuctionItem 모델에 맞는 데이터 파싱 - 실제 모델 필드에만 매핑"""
        dspsl_info = dma_result.get('dspslGdsDxdyInfo', {})
        objct_info = dma_result.get('gdsDspslObjctLst', [{}])[0] if dma_result.get('gdsDspslObjctLst') else {}
        
        # 이미지 URL 구성
        image_urls = []
        for pic in dma_result.get('csPicLst', []):
            image_url = f"https://www.courtauction.go.kr{pic.get('picFileUrl', '')}{pic.get('picTitlNm', '')}"
            image_urls.append(image_url)
        
        # 물건 용도 매핑
        usage_mapping = {
            '20104': '아파트',
            '20100': '주택',
            '10000': '토지',
            '30000': '상업용부동산',
            '01': '부동산'
        }
        item_purpose = usage_mapping.get(objct_info.get('sclDspslGdsLstUsgCd', ''), '부동산')
        
        # AuctionItem 모델의 실제 필드들만 매핑
        item_data = {
            'case_number': auction_case,
            'item_number': dspsl_info.get('dspslGdsSeq', 1),
            'item_spec_url': dspsl_info.get('orvParam', ''),  # 실제 API에서 제공하는 필드명
            'item_purpose': item_purpose,
            'valuation_amount': str(dspsl_info.get('aeeEvlAmt', 0)),
            'item_note': self.extract_item_notes(dma_result),
            'item_status': '매각공고',  # 기본값
            'auction_date': self.parse_datetime_from_api_schedule(dma_result),
            'auction_failures': dspsl_info.get('flbdNcnt', 0),
            'item_image_url': image_urls[0] if image_urls else None,
            'view_count': 0,  # 기본값
        }
        
        # 경매 일정 정보 파싱 (최대 4회차까지)
        schedule_info = self.parse_auction_schedule(dma_result)
        item_data.update(schedule_info)
        
        return item_data
    
    def parse_auction_schedule(self, dma_result: Dict[str, Any]) -> Dict[str, Any]:
        """경매 일정 정보 파싱"""
        schedule = {}
        
        # gdsDspslDxdyLst에서 경매 일정 정보 추출
        auction_schedules = dma_result.get('gdsDspslDxdyLst', [])
        
        for i, schedule_item in enumerate(auction_schedules[:4], 1):  # 최대 4회차
            auction_date_field = f'auction_date_{i}'
            decision_date_field = f'decision_date_{i}'
            
            # 경매 일자
            auction_date = self.parse_datetime_from_date_and_time(
                schedule_item.get('dspslDxdyYmd', ''),
                schedule_item.get('dspslHm', '')
            )
            schedule[auction_date_field] = auction_date
            
            # 결정 일자 (있다면)
            decision_date = self.parse_datetime_from_date_and_time(
                schedule_item.get('dcsnDxdyYmd', ''),
                schedule_item.get('dcsnHm', '')
            )
            schedule[decision_date_field] = decision_date
        
        # 빈 필드들을 None으로 채움
        for i in range(1, 5):
            if f'auction_date_{i}' not in schedule:
                schedule[f'auction_date_{i}'] = None
            if f'decision_date_{i}' not in schedule:
                schedule[f'decision_date_{i}'] = None
        
        return schedule
    
    def parse_datetime_from_api_schedule(self, dma_result: Dict[str, Any]) -> Optional[datetime]:
        """API에서 다음 경매 일정 추출"""
        schedules = dma_result.get('gdsDspslDxdyLst', [])
        
        # 가장 최근/다음 경매 일정 찾기
        for schedule_item in schedules:
            auction_date = self.parse_datetime_from_date_and_time(
                schedule_item.get('dspslDxdyYmd', ''),
                schedule_item.get('dspslHm', '')
            )
            if auction_date:
                return auction_date
        
        return None
    
    def extract_item_notes(self, dma_result: Dict[str, Any]) -> str:
        """감정평가 내용을 종합하여 물건 비고 생성"""
        notes = []
        
        # 감정평가 요점 정보
        for eval_point in dma_result.get('aeeWevlMnpntLst', []):
            content = eval_point.get('aeeWevlMnpntCtt', '').strip()
            if content and content != '-':
                notes.append(content)
        
        # 권리관계 정보
        dspsl_info = dma_result.get('dspslGdsDxdyInfo', {})
        if dspsl_info.get('tprtyRnkHypthcStngDts'):
            notes.append(f"권리관계: {dspsl_info.get('tprtyRnkHypthcStngDts')}")
        
        # 물건 비고
        if dspsl_info.get('dspslGdsRmk'):
            notes.append(dspsl_info.get('dspslGdsRmk'))
        
        return ' | '.join(notes[:3])  # 처음 3개만 사용, 너무 길지 않게
    
    def save_auction_case(self, case_data: Dict[str, Any]):
        """AuctionCase 저장"""
        auction_case, created = AuctionCase.objects.get_or_create(
            case_number=case_data['case_number'],
            defaults=case_data
        )
        
        if not created:
            # 기존 데이터 업데이트
            for key, value in case_data.items():
                setattr(auction_case, key, value)
            auction_case.save()
        
        self.logger.info(f"AuctionCase {'생성' if created else '업데이트'}: {case_data['case_number']}")
        return auction_case
    
    def save_auction_item(self, item_data: Dict[str, Any]):
        """AuctionItem 저장"""
        auction_item, created = AuctionItem.objects.get_or_create(
            case_number=item_data['case_number'],
            item_number=item_data['item_number'],
            defaults=item_data
        )
        
        if not created:
            # 기존 데이터 업데이트
            for key, value in item_data.items():
                setattr(auction_item, key, value)
            auction_item.save()
        
        self.logger.info(f"AuctionItem {'생성' if created else '업데이트'}: {item_data['case_number']}-{item_data['item_number']}")
        return auction_item
    
    def parse_date(self, date_str: str) -> Optional[date]:
        """YYYYMMDD 형식의 날짜 문자열을 date 객체로 변환"""
        if not date_str:
            return None
        try:
            if len(date_str) == 8 and date_str.isdigit():
                return datetime.strptime(date_str, '%Y%m%d').date()
            return None
        except ValueError:
            return None
    
    def parse_datetime_from_date_and_time(self, date_str: str, time_str: str) -> Optional[datetime]:
        """날짜와 시간 문자열을 datetime 객체로 변환"""
        if not date_str:
            return None
        
        try:
            # YYYYMMDD 형식의 날짜만 있는 경우
            if len(date_str) == 8 and date_str.isdigit():
                if time_str and len(time_str) == 4 and time_str.isdigit():
                    # 시간도 있는 경우
                    datetime_str = date_str + time_str
                    return datetime.strptime(datetime_str, '%Y%m%d%H%M')
                else:
                    # 날짜만 있는 경우 (기본 시간 10:00 설정)
                    datetime_str = date_str + '1000'
                    return datetime.strptime(datetime_str, '%Y%m%d%H%M')
            return None
        except ValueError:
            return None
    
    def save_to_json(self, data: Dict[str, Any], filename: str) -> bool:
        """데이터를 JSON 파일로 저장"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            self.logger.info(f"데이터가 {filename}에 저장되었습니다.")
            return True
        except Exception as e:
            self.logger.error(f"파일 저장 중 오류: {str(e)}")
            return False

# Django 관리 명령
def main():
    parser = CourtAuctionParser()
    
    # 사건번호 입력 받기
    case_number = input("사건번호를 입력하세요 (예: 2022타경113322): ")
    
    print(f"사건번호 {case_number}의 경매 정보를 가져오는 중...")
    
    # API에서 데이터 가져오기
    raw_data = parser.fetch_auction_data(case_number)
    
    if raw_data:
        print("API 응답을 받았습니다.")
        
        # 데이터 파싱 및 저장
        result = parser.parse_and_save_auction_data(raw_data)
        
        if result:
            print(f"저장 완료:")
            print(f"- 사건: {result['case'].case_number} - {result['case'].case_name}")
            print(f"- 물건: {result['item'].item_purpose} ({result['item'].valuation_amount}원)")
            
            # JSON으로도 저장
            parser.save_to_json(result['raw_data'], f'auction_data_{case_number}.json')
        else:
            print("데이터 파싱/저장에 실패했습니다.")
    else:
        print("API 응답을 받지 못했습니다.")

if __name__ == "__main__":
    main()