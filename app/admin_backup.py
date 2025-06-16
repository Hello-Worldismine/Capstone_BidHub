from django.contrib import admin
from django.ut@admin.register(AuctionItem)
class AuctionItemAdmin(admin.ModelAdmin):
    list_display = ('property_name', 'case_number', 'auction_date', 'current_min_price', 'item_status', 'image_preview')
    search_fields = ('property_name', 'case_number__case_number', 'property_address')
    list_filter = ('item_status', 'property_type', 'auction_date')
    ordering = ('-auction_date',)
    actions = ['upload_images_action']
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('case_number', 'item_number', 'property_name', 'item_purpose')
        }),
        ('위치 정보', {
            'fields': ('property_address', 'property_detail_address', 'floor_info')
        }),
        ('물건 상세', {
            'fields': ('property_type', 'building_area', 'item_note')
        }),
        ('이미지', {
            'fields': ('item_image_url', 'current_image_preview', 'upload_new_images_link'),
            'description': '이미지 번호를 입력하거나 새 이미지를 업로드하세요. 사용 가능한 번호: ' + ', '.join(get_available_image_folders()[:10]) + ('...' if len(get_available_image_folders()) > 10 else '')
        }),
        ('경매 정보', {
            'fields': ('auction_date', 'auction_failures', 'item_status')
        }),
        ('금액 정보', {
            'fields': ('valuation_amount', 'current_min_price', 'deposit_amount')
        }),
    )
    
    readonly_fields = ('case_number_info', 'current_image_preview', 'upload_new_images_link')
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-images/<int:item_id>/', self.upload_images_view, name='auctionitem_upload_images'),
        ]
        return custom_urls + urls
    
    def upload_images_view(self, request, item_id):
        """이미지 업로드 뷰"""
        try:
            item = AuctionItem.objects.get(id=item_id)
        except AuctionItem.DoesNotExist:
            messages.error(request, '매물을 찾을 수 없습니다.')
            return redirect('..')
        
        if request.method == 'POST':
            form = ImageUploadForm(request.POST, request.FILES)
            if form.is_valid():
                try:
                    new_folder_number = form.save_images()
                    item.item_image_url = new_folder_number
                    item.save()
                    messages.success(request, f'이미지가 성공적으로 업로드되었습니다. 새 이미지 번호: {new_folder_number}')
                    return redirect('admin:app_auctionitem_change', item.id)
                except Exception as e:
                    messages.error(request, f'이미지 업로드 중 오류가 발생했습니다: {str(e)}')
        else:
            form = ImageUploadForm()
        
        return render(request, 'admin/app/auctionitem/upload_images.html', {
            'form': form,
            'item': item,
            'title': f'{item.property_name} - 이미지 업로드'
        })
    
    def upload_images_action(self, request, queryset):
        """선택된 매물들에 대한 이미지 업로드 액션"""
        if queryset.count() != 1:
            messages.error(request, '이미지 업로드는 한 번에 하나의 매물만 선택해주세요.')
            return
        
        item = queryset.first()
        return HttpResponseRedirect(f'upload-images/{item.id}/')
    
    upload_images_action.short_description = "선택된 매물에 새 이미지 업로드"
    
    def upload_new_images_link(self, obj):
        """새 이미지 업로드 링크"""
        if obj.id:
            return format_html(
                '<a href="upload-images/{}" class="button">새 이미지 업로드</a>',
                obj.id
            )
        return "매물을 먼저 저장한 후 이미지를 업로드할 수 있습니다."
    upload_new_images_link.short_description = "이미지 업로드"ml import format_html
from django.conf import settings
from django.shortcuts import render, redirect
from django.urls import path
from django.http import HttpResponseRedirect
from django.contrib import messages
import os
from .models import AuctionCase, AuctionItem, ClaimDistribution, AuctionParty, PropertyListing
from .forms import ImageUploadForm

# Admin 사이트 커스터마이징
admin.site.site_header = "BidHub 관리자"
admin.site.site_title = "BidHub Admin"
admin.site.index_title = "경매 매물 관리"

def get_available_image_folders():
    """사용 가능한 이미지 폴더 목록을 반환합니다."""
    itemimages_path = os.path.join(settings.BASE_DIR, 'main', 'static', 'img', 'itemimages')
    if os.path.exists(itemimages_path):
        folders = [f for f in os.listdir(itemimages_path) 
                  if os.path.isdir(os.path.join(itemimages_path, f)) and f.isdigit()]
        return sorted(folders)
    return []

@admin.register(AuctionCase)
class AuctionCaseAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'case_name', 'court_name', 'filing_date', 'case_status')
    search_fields = ('case_number', 'case_name', 'court_name')
    list_filter = ('court_name', 'case_status', 'filing_date')
    ordering = ('-filing_date',)
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('case_number', 'case_name', 'court_name', 'filing_date')
        }),
        ('담당 및 상태', {
            'fields': ('responsible_dept', 'case_status', 'appeal_status')
        }),
        ('금액 정보', {
            'fields': ('claim_amount', 'minimum_bid_price')
        }),
        ('결과', {
            'fields': ('final_result', 'final_date'),
            'classes': ('collapse',)
        }),
    )

@admin.register(AuctionItem)
class AuctionItemAdmin(admin.ModelAdmin):
    list_display = ('property_name', 'case_number', 'auction_date', 'current_min_price', 'item_status', 'image_preview')
    search_fields = ('property_name', 'case_number__case_number', 'property_address')
    list_filter = ('item_status', 'property_type', 'auction_date')
    ordering = ('-auction_date',)
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('case_number', 'item_number', 'property_name', 'item_purpose')
        }),
        ('위치 정보', {
            'fields': ('property_address', 'property_detail_address', 'floor_info')
        }),
        ('물건 상세', {
            'fields': ('property_type', 'building_area', 'item_note')
        }),
        ('이미지', {
            'fields': ('item_image_url', 'current_image_preview'),
            'description': '이미지 번호를 입력하세요. 사용 가능한 번호: ' + ', '.join(get_available_image_folders()[:10]) + ('...' if len(get_available_image_folders()) > 10 else '')
        }),
        ('경매 정보', {
            'fields': ('auction_date', 'auction_failures', 'item_status')
        }),
        ('금액 정보', {
            'fields': ('valuation_amount', 'current_min_price', 'deposit_amount')
        }),
    )
    
    readonly_fields = ('case_number_info', 'current_image_preview')
    
    def case_number_info(self, obj):
        if obj.case_number:
            return f"{obj.case_number.case_number} - {obj.case_number.case_name}"
        return "케이스 없음"
    case_number_info.short_description = "사건 정보"
    
    def image_preview(self, obj):
        """목록에서 보여줄 작은 이미지 미리보기"""
        if obj.item_image_url:
            image_url = f"/static/img/itemimages/{obj.item_image_url}/img_1_wm.jpg"
            return format_html(
                '<img src="{}" width="50" height="50" style="object-fit: cover;" />',
                image_url
            )
        return "이미지 없음"
    image_preview.short_description = "미리보기"
    
    def current_image_preview(self, obj):
        """상세 편집 페이지에서 보여줄 이미지 미리보기"""
        if obj.item_image_url:
            images_html = ""
            for i in range(1, 6):  # 첫 5개 이미지 표시
                image_url = f"/static/img/itemimages/{obj.item_image_url}/img_{i}_wm.jpg"
                images_html += f'<img src="{image_url}" width="100" height="100" style="margin: 5px; object-fit: cover;" onerror="this.style.display=\'none\'" />'
            
            return format_html(
                '<div style="margin: 10px 0;">'
                '<p><strong>현재 이미지 폴더:</strong> {}</p>'
                '<div>{}</div>'
                '<p><small>이미지 폴더 번호를 변경하면 다른 이미지 세트가 표시됩니다.</small></p>'
                '</div>',
                obj.item_image_url,
                images_html
            )
        return "이미지를 보려면 이미지 번호를 입력하세요."
    current_image_preview.short_description = "현재 이미지"

@admin.register(PropertyListing)
class PropertyListingAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'listing_type', 'location', 'final_result')
    search_fields = ('case_number__case_number', 'location', 'details')
    list_filter = ('listing_type', 'final_result')
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('case_number', 'listing_type', 'location')
        }),
        ('상세 설명', {
            'fields': ('details',)
        }),
        ('결과', {
            'fields': ('final_result', 'final_date'),
            'classes': ('collapse',)
        }),
    )

@admin.register(ClaimDistribution)
class ClaimDistributionAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'location', 'claim_deadline')
    search_fields = ('case_number__case_number', 'location')
    list_filter = ('claim_deadline',)
    ordering = ('-claim_deadline',)

@admin.register(AuctionParty)
class AuctionPartyAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'party_type', 'party_name', 'remarks')
    search_fields = ('case_number__case_number', 'party_name')
    list_filter = ('party_type',)
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('case_number', 'party_type', 'party_name')
        }),
        ('추가 정보', {
            'fields': ('remarks',)
        }),
    )
