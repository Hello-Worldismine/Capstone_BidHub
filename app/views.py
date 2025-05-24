from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import AuctionItem, AuctionCase
from .serializers import AuctionItemSerializer, AuctionCaseSerializer
from django.http import JsonResponse
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os

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