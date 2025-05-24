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
    auction_items = AuctionItem.objects.all() # Fetch all items for now
    context = {
        'auction_items': auction_items
    }
    return render(request, 'index.html', context) # Pass context to the template

def tender(request):
    return render(request, 'tender.html')

def auto_bid(request):
    return render(request, 'auto_bid.html')

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
    return render(request, 'mypage.html', context)

def bidform(request):
    return render(request, 'bidform.html')

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

    return render(request, 'charge.html', {'balance': profile.balance if profile else 0})

def property_detail(request, case_number):
    try:
        # Try to find the auction case with the provided case number
        case = get_object_or_404(AuctionCase, case_number=case_number)
        item_details = AuctionItem.objects.filter(case_number=case).first()
        
        # Get related data for display
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
        
        # 소재지 정보 (배당요구 정보)
        location_info = {
            'location': claim_distribution.location if claim_distribution else None,
            'claim_deadline': claim_distribution.claim_deadline if claim_distribution else None,
            'case_number': case.case_number if case else None
        }
        
        # 문서 URL
        document_urls = {
            'specification_url': item_details.item_spec_url
        }
        
        # 입찰 내역 현황 - 경매 일정 정보 제공
        bidding_history = []
        
        # Parse the valuation amount to a number safely for calculations
        try:
            val_amount_str = item_details.valuation_amount or "0"
            # Remove non-numeric characters except for decimal points
            val_amount_str = ''.join(c for c in val_amount_str if c.isdigit() or c == '.')
            valuation_amount = float(val_amount_str)
        except (ValueError, TypeError):
            valuation_amount = 0
            
        # 경매 일정 데이터 추가
        if item_details.auction_date_1:
            bidding_history.append({
                'id': 1,
                'link_text': f"{case.case_number} 1차 입찰",
                'type': '1차 입찰',
                'min_price': item_details.valuation_amount,
                'status': '유찰' if item_details.auction_failures > 0 else '진행중',
                'price_details': f"{item_details.valuation_amount} / {int(valuation_amount * 0.8):,} / {int(valuation_amount * 0.1):,}",
                'auction_date': item_details.auction_date_1,
                'due_date': item_details.decision_date_1
            })
        
        if item_details.auction_date_2:
            bidding_history.append({
                'id': 2,
                'link_text': f"{case.case_number} 2차 입찰",
                'type': '2차 입찰',
                'min_price': f"{int(valuation_amount * 0.8):,}",
                'status': '유찰' if item_details.auction_failures > 1 else '진행중',
                'price_details': f"{item_details.valuation_amount} / {int(valuation_amount * 0.64):,} / {int(valuation_amount * 0.08):,}",
                'auction_date': item_details.auction_date_2,
                'due_date': item_details.decision_date_2
            })
        
        if item_details.auction_date_3:
            bidding_history.append({
                'id': 3,
                'link_text': f"{case.case_number} 3차 입찰",
                'type': '3차 입찰',
                'min_price': f"{int(valuation_amount * 0.64):,}",
                'status': '유찰' if item_details.auction_failures > 2 else '진행중',
                'price_details': f"{item_details.valuation_amount} / {int(valuation_amount * 0.512):,} / {int(valuation_amount * 0.064):,}",
                'auction_date': item_details.auction_date_3,
                'due_date': item_details.decision_date_3
            })
        
        if item_details.auction_date_4:
            bidding_history.append({
                'id': 4,
                'link_text': f"{case.case_number} 4차 입찰",
                'type': '4차 입찰',
                'min_price': f"{int(valuation_amount * 0.512):,}",
                'status': '진행중',
                'price_details': f"{item_details.valuation_amount} / {int(valuation_amount * 0.4096):,} / {int(valuation_amount * 0.0512):,}",
                'auction_date': item_details.auction_date_4,
                'due_date': item_details.decision_date_4
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
        
        return render(request, 'property_detail.html', context)
        
    except AuctionItem.DoesNotExist:
        return redirect('index')

def get_favorite_properties(request):
    from main.models import FavoriteProperty 
    favorites = FavoriteProperty.objects.all()
    data = [
        {'case_number': fav.case_number, 'usage': fav.usage}
        for fav in favorites
    ]
    return JsonResponse({'success': True, 'favorites': data})