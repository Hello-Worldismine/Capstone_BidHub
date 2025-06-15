from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import AuctionItem, AuctionCase, BidLog
from .serializers import AuctionItemSerializer, AuctionCaseSerializer
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db.models.functions import Lower
from web3 import Web3
from eth_account.messages import encode_defunct
import os
import json
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpRequest
import logging
import requests
from django.utils.dateparse import parse_date
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)
from .graph_query import fetch_trade_closes

from blockchain.contracts import (
    putsec, inputbid, pay_for_award,
    mark_additional_bid, withdraw, escrow_deposit,
    escrow_refund, confirm_bid, 
    get_nonce, view_deposits, get_balance
)

from blockchain.crypto import (
    encrypt_bid_data, decrypt_aes, deserialize_decrypted_data
)

GRAPHQL_URL = "https://api.studio.thegraph.com/query/111711/capstone/version/latest"

@api_view(['GET'])
def all_cases(request):
    cases = AuctionCase.objects.all()
    serializer = AuctionCaseSerializer(cases, many=True)
    return Response(serializer.data)


def auction_detail(request, item_id):
    try:
        item = AuctionItem.objects.get(item_number=item_id)
        case = item.case_number

        data = {
            'item': {
                'item_number': item.item_number,
                'item_spec_url': item.item_spec_url,
                'item_purpose': item.item_purpose,
                'valuation_amount': item.valuation_amount,
                'item_status': item.item_status,
                'auction_date': item.auction_date,
            },
            'case': {
                'case_number': case.case_number,
                'case_name': case.case_name,
                'court_name': case.court_name,
                'filing_date': case.filing_date,
                'claim_amount': case.claim_amount,
            },
            'claims': list(case.claimdistribution_set.values('id', 'location', 'claim_deadline')),
            'parties': list(case.auctionparty_set.values('id', 'party_type', 'party_name')),
            'listings': list(case.propertylisting_set.values('id', 'location', 'listing_type', 'details')),
        }

        return JsonResponse(data)
    except AuctionItem.DoesNotExist:
        return JsonResponse({'error': '해당 물건을 찾을 수 없습니다.'}, status=404)

def auction_list(request):
    court_name = request.GET.get('court_name')
    
    items = AuctionItem.objects.select_related('case_number').all()

    if court_name:
        items = items.filter(case_number__court_name=court_name)

    data = []
    for item in items:
        data.append({
            'case_number': item.case_number.case_number if item.case_number else None,
            'min_bid': item.valuation_amount,
            'auction_failures': item.auction_failures,
            'deadline': item.auction_date.strftime('%Y-%m-%d %H:%M') if item.auction_date else None,
        })

    return JsonResponse(data, safe=False)

@api_view(['POST'])
def upload_property_image(request, item_id):
    try:
        item = AuctionItem.objects.get(item_number=item_id)
        image_file = request.FILES.get('image')
        
        if image_file:
            # 이미지 파일 저장
            path = default_storage.save(f'property_images/{item_id}_{image_file.name}', ContentFile(image_file.read()))
            
            # 이미지 URL 저장
            image_url = default_storage.url(path)
            if item.item_image_url:
                item.item_image_url = image_url
            else:
                item.item_image_url = image_url
                
            item.save()
            
            return Response({
                'success': True,
                'message': '이미지가 성공적으로 업로드되었습니다.',
                'image_url': image_url
            })
        else:
            return Response({
                'success': False,
                'message': '이미지 파일이 제공되지 않았습니다.'
            }, status=400)
            
    except AuctionItem.DoesNotExist:
        return Response({
            'success': False,
            'message': '해당 매물을 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)

@api_view(['POST'])
def bulk_upload_images(request, item_id):
    try:
        item = AuctionItem.objects.get(item_number=item_id)
        images = request.FILES.getlist('images')
        
        if not images:
            return Response({
                'success': False,
                'message': '이미지 파일이 제공되지 않았습니다.'
            }, status=400)
            
        uploaded_images = []
        for image in images:
            # 이미지 파일 저장
            path = default_storage.save(f'property_images/{item_id}_{image.name}', ContentFile(image.read()))
            # URL 저장
            image_url = default_storage.url(path)
            uploaded_images.append({
                'filename': image.name,
                'url': image_url
            })
            
        # 여러 이미지 URL을 저장할 수 있도록 item_image_url 필드 업데이트
        if item.item_image_url:
            existing_urls = item.item_image_url.split(',')
            new_urls = [img['url'] for img in uploaded_images]
            item.item_image_url = ','.join(existing_urls + new_urls)
        else:
            item.item_image_url = ','.join([img['url'] for img in uploaded_images])
        
        item.save()
        
        return Response({
            'success': True,
            'message': f'{len(uploaded_images)}개의 이미지가 성공적으로 업로드되었습니다.',
            'uploaded_images': uploaded_images
        })
            
    except AuctionItem.DoesNotExist:
        return Response({
            'success': False,
            'message': '해당 매물을 찾을 수 없습니다.'
        }, status=404)
    except Exception as e:
        return Response({
            'success': False,
            'message': str(e)
        }, status=500)
        



#블록체인 관련 api
@api_view(['POST'])
def inputbid_api(request):
    try:
        print(100)
        data = json.loads(request.body)

        trade_num = int(data.get("trade_num"))
        amount = int(data.get("amount"))
        security = int(data.get("security"))
        bidder = data.get("bidder")
        bid_time = int(data.get("bid_time"))

        # 스마트 컨트랙트 트랜잭션 실행
        tx_result = inputbid(trade_num, amount, security, bidder, bid_time)

        return JsonResponse({
            "status": tx_result.get("status"),
            "tx_hash": tx_result.get("tx_hash"),
            "trade_num": trade_num,
            "amount": amount,
            "security": security,
            "bidder": bidder,
            "bid_time": bid_time
        })

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=400)

        
def pay_for_award_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        result = pay_for_award(
            data['amount'], data['trade_num'],
            data['bidder'], data['nonce'], data['signature']
        )
        return JsonResponse(result)



def mark_additional_bid_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        result = mark_additional_bid(
            data['trade_num'], data['bidder'],
            data['nonce'], data['signature']
        )
        return JsonResponse(result)



from django.http import JsonResponse

@csrf_exempt
def withdraw_api(request):
    try:
        data = json.loads(request.body)
        amount = int(data.get("amount"))
        to_address = data.get("to_address")
        nonce = int(data.get("nonce"))
        signature = data.get("signature")

        result = withdraw(amount, to_address, nonce, signature)

        if result["status"] == "success":
            return JsonResponse({"success": True, "tx_hash": result["tx_hash"]})
        else:
            return JsonResponse({"success": False, "message": result.get("message", "출금 실패")})

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)})



def escrow_deposit_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        result = escrow_deposit(data['amount'])
        return JsonResponse(result)



def confirm_bid_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        result = confirm_bid(data['trade_num'])
        return JsonResponse({"winner": result[0], "amount": result[1]})




def get_nonce_api(request):
    if request.method == 'GET':
        user = request.GET.get('user')
        action_index = int(request.GET.get('action_index'))
        result = get_nonce(user, action_index)
        return JsonResponse({"nonce": result})


from datetime import datetime

@api_view(['POST'])
def putsec_api(request):
    try:
        data = json.loads(request.body)

        trade_num = int(data["trade_num"])
        bidder = data["bidder"]
        security = int(data["security"])
        nonce = int(data["nonce"])
        signature = data["signature"]
        bid_time = int(data["bid_time"])
        amount = int(data["amount"])  # 🔸 입찰금액 반드시 받아야 함

        tx_result = putsec(trade_num, bidder, security, nonce, signature)

        if tx_result["status"] == "success":
            BidLog.objects.update_or_create(
                trade_num=trade_num,
                bidder_address=bidder,
                defaults={
                    "bid_amount": amount,
                    "bid_security": security,
                    "bid_time": datetime.fromtimestamp(bid_time)
                }
            )

            return JsonResponse({
                "status": "success",
                "tx_hash": tx_result["tx_hash"]
            })
        else:
            return JsonResponse({
                "status": tx_result["status"],
                "message": tx_result.get("message", "실패 사유 없음"),
                "tx_hash": tx_result.get("tx_hash")
            }, status=400)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)

def view_deposits_api(request):
    if request.method == 'GET':
        user = request.GET.get('user')  # 지갑 주소
        result_wei = view_deposits(user)  # 이더 입금량(wei 단위)
        krw = int(result_wei) * 10000000000 / 1e18  # 1 ETH = 100억 원
        return JsonResponse({
            "deposits_wei": result_wei,
            "deposits_krw": round(krw)
        })

def get_balance_api(request):
    if request.method == 'GET':
        result = get_balance()
        return JsonResponse({"balance_wei": result})
    
def escrow_withdraw_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            trade_num = int(data.get("trade_num"))
            result = escrow_refund(trade_num)
            return JsonResponse(result)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request"}, status=405)


def store_encrypted_bid(request):
    if request.method == "POST":
        data = json.loads(request.body)
        trade_num = int(data["trade_num"])
        bidder = data["bidder"].lower()
        amount = int(data["bid_amount"])
        
        BidLog.objects.update_or_create(
            trade_num=trade_num,
            bidder_address=bidder,
            defaults={"bid_amount": amount}
        )

        return JsonResponse({"status": "success"})

def load_bid_history(request):
    user_address = request.user.profile.wallet_address.lower()
    
    logger.warning(f"로그인된 주소: {request.user.profile.wallet_address}")
    logger.warning(f"소문자 주소: {user_address}")

    bid_logs = BidLog.objects.filter(bidder_address__iexact=user_address)
    logger.warning(f"조회된 BidLog 개수: {bid_logs.count()}")
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
          putCrypts(where: {{tradeNum: "{trade_num}", bidder: "{user_address}"}}) {{
            security
          }}
          refundSecurities(where: {{tradeNum: "{trade_num}", bidder: "{user_address}"}}) {{
            timestamp
          }}
        }}
        """
        res = requests.post(GRAPHQL_URL, json={'query': graphql_query})
        data = res.json().get("data", {})

        security_data = data.get("putCrypts", [])
        security = int(security_data[0]["security"]) if security_data else 0

        refund_data = data.get("refundSecurities", [])
        if refund_data:
            refund_status = "완료"
            refund_date = datetime.fromtimestamp(int(refund_data[0]["timestamp"])).strftime("%Y-%m-%d")
        else:
            refund_status = "처리중"
            refund_date = "-"

        bid_rows.append({
            "case_number": case_number,
            "bid_amount": f"{bid_amount:,}" if isinstance(bid_amount, int) else bid_amount,
            "security": f"{security:,}원",
            "refund_status": refund_status,
            "refund_date": refund_date
        })
        print(f"{log.trade_num=} {log.bid_amount=} {log.bidder_address=}")



    return render(request, "main/pages/bid_history.html", {"bid_rows": bid_rows})


def result_view(request):
    court = request.GET.get("court")
    property_type = request.GET.get("property_type")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    filters_applied = any([court, property_type, start_date, end_date])
    results = []

    for event in fetch_trade_closes():
        try:
            item = AuctionItem.objects.get(case_number__case_number__contains=str(event["trade_num"]))

            if court and court not in item.case_number.court_name:
                continue
            if property_type and property_type not in (item.item_purpose or ""):
                continue
            if start_date and event["auction_date"] < datetime.strptime(start_date, "%Y-%m-%d").timestamp():
                continue
            if end_date and event["auction_date"] > datetime.strptime(end_date, "%Y-%m-%d").timestamp():
                continue

            results.append({
                "case_number": item.case_number.case_number,
                "court_name": item.case_number.court_name,
                "case_name": item.case_number.case_name,
                "valuation_amount": item.valuation_amount,
                "auction_failures": item.auction_failures,
                "item_purpose": item.item_purpose,
                "item_note": item.item_note,
                "auction_date": datetime.fromtimestamp(event["auction_date"]),
            })
        except AuctionItem.DoesNotExist:
            continue

    return render(request, "result.html", {
        "search_results": results,
        "search_performed": filters_applied,  # 중요!
        "search_error": None  # 오류 있을 시 추가
    })
    

def result_api_view(request):
    court = request.GET.get("court")
    property_type = request.GET.get("property_type")
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    results = []
    for event in fetch_trade_closes():
        try:
            item = AuctionItem.objects.get(case_number__case_number__contains=str(event["trade_num"]))

            # 필터 조건 적용
            if court and court not in item.case_number.court_name:
                continue
            if property_type and property_type not in (item.item_purpose or ""):
                continue
            if start_date:
                if event["auction_date"] < datetime.strptime(start_date, "%Y-%m-%d").timestamp():
                    continue
            if end_date:
                if event["auction_date"] > datetime.strptime(end_date, "%Y-%m-%d").timestamp():
                    continue

            results.append({
                "case_number": item.case_number.case_number,
                "court_name": item.case_number.court_name,
                "case_name": item.case_number.case_name,
                "auction_item": {
                    "valuation_amount": item.valuation_amount,
                    "auction_failures": item.auction_failures,
                    "item_purpose": item.item_purpose,
                    "item_note": item.item_note,
                    "auction_date": datetime.fromtimestamp(event["auction_date"]).strftime("%Y-%m-%d %H:%M"),
                }
            })
        except AuctionItem.DoesNotExist:
            continue

    return JsonResponse(results, safe=False)

def region_trade_results_api(request):
    sido = request.GET.get("sido")
    sigugun = request.GET.get("sigugun")
    load_initial = request.GET.get("load")  # 'ㄱ', 'ㄴ', 또는 전체 도로명

    queryset = AuctionCase.objects.all()

    if sido:
        queryset = queryset.filter(location__sido__icontains=sido)
    if sigugun:
        queryset = queryset.filter(location__sigugun__icontains=sigugun)

    # 도로명 필터링: 자음만 들어온 경우 초성별 범위 처리
    if load_initial:
        초성_범위 = {
            "ㄱ": ("가", "나"),
            "ㄴ": ("나", "다"),
            "ㄷ": ("다", "라"),
            "ㄹ": ("라", "마"),
            "ㅁ": ("마", "바"),
            "ㅂ": ("바", "사"),
            "ㅅ": ("사", "아"),
            "ㅇ": ("아", "자"),
            "ㅈ": ("자", "차"),
            "ㅊ": ("차", "카"),
            "ㅋ": ("카", "타"),
            "ㅌ": ("타", "파"),
            "ㅍ": ("파", "하"),
            "ㅎ": ("하", "힣"),
        }

        if load_initial in 초성_범위:
            start, end = 초성_범위[load_initial]
            queryset = queryset.filter(location__load__gte=start, location__load__lt=end)
        else:
            queryset = queryset.filter(location__load__icontains=load_initial)

    # 결과 가공
    results = []
    for case in queryset:
        item = case.auctionitem_set.order_by("-auction_date").first()
        results.append({
            "case_number": case.case_number,
            "court_name": case.court_name,
            "case_name": case.case_name,
            "auction_item": {
                "valuation_amount": item.valuation_amount if item else None,
                "auction_failures": item.auction_failures if item else None,
                "item_purpose": item.item_purpose if item else None,
                "item_note": item.item_note if item else None,
                "auction_date": item.auction_date.strftime("%Y-%m-%d %H:%M") if item and item.auction_date else None,
            } if item else None
        })

    return JsonResponse(results, safe=False)

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
#임시 더미
def dummy_view(request):
    return JsonResponse({"message": "미구현된 API입니다."})