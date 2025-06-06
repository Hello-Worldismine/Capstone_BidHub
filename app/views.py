from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import AuctionItem, AuctionCase
from .serializers import AuctionItemSerializer, AuctionCaseSerializer
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from web3 import Web3
from eth_account.messages import encode_defunct
import os
import json
from blockchain.contracts import (
    put_cryptogram, input_decrypt, pay_for_award,
    mark_additional_bid, withdraw, escrow_deposit,
    escrow_refund, confirm_bid, get_cryptogram,
    get_nonce, view_deposits, get_balance
)

from blockchain.crypto import (
    encrypt_bid_data, decrypt_aes, deserialize_decrypted_data
)

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
def decode_and_input_decrypt_api(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            trade_num = int(data.get("trade_num"))
            due_date = int(data.get("due_date"))  # 낙찰 마감일 (유닉스 타임)

            # 1. 암호화 데이터 가져오기
            chunks = get_cryptogram(trade_num)
            if len(chunks) < 3:
                return JsonResponse({"status": "error", "message": "암호화 데이터 없음"}, status=404)

            # 2. 조립하여 복호화
            iv_and_ciphertext = b''.join([
                chunks[0].to_bytes(32, 'big'),
                chunks[1].to_bytes(32, 'big'),
                chunks[2].to_bytes(32, 'big'),
            ])
            decrypted = decrypt_aes(iv_and_ciphertext)
            parsed = deserialize_decrypted_data(decrypted)

            # 3. inputDecrypt 트랜잭션 실행
            result = input_decrypt(
                parsed["trade_num"],
                parsed["amount"],
                parsed["security"],
                parsed["bidder"],
                parsed["bid_time"],
                due_date
            )

            return JsonResponse({
                "status": result.get("status"),
                "tx_hash": result.get("tx_hash"),
                **parsed
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


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



def withdraw_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        result = withdraw(
            data['amount'], data['to_address'],
            data['nonce'], data['signature']
        )
        return JsonResponse(result)



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

@api_view(['POST'])
def encrypt_bid_api(request):
    try:
        data = json.loads(request.body)
        trade_num = int(data.get("trade_num"))
        amount = int(data.get("amount"))
        security = int(data.get("security"))
        bidder = data.get("bidder")
        bid_time = int(data.get("bid_time"))

        # 암호화 및 분할
        chunks = encrypt_bid_data(trade_num, amount, security, bidder, bid_time)  # [P1, P2, P3]

        return JsonResponse({
            "status": "success",
            "chunks": chunks
        })
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=400)
    

@api_view(['POST'])
def put_cryptogram_api(request):
    try:
        data = json.loads(request.body)

        trade_num = int(data["trade_num"])
        p1 = int(data["p1"])
        p2 = int(data["p2"])
        p3 = int(data["p3"])
        bidder = data["bidder"]
        security = int(data["security"])
        nonce = int(data["nonce"])
        signature = data["signature"]

        tx_result = put_cryptogram(trade_num, p1, p2, p3, bidder, security, nonce, signature)
        
        if tx_result["status"] == "success":
            return JsonResponse({
                "status": "success",
                "tx_hash": tx_result["tx_hash"]
                })
        else:
            return JsonResponse({
                "status": tx_result["status"],
                "message": tx_result.get("message", "실패 사유 없음"),
                "tx_hash": tx_result.get("tx_hash")  # 있으면 같이 보내줌
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

#임시 더미
def dummy_view(request):
    return JsonResponse({"message": "미구현된 API입니다."})