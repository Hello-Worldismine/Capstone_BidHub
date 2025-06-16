from django.contrib import admin
from .models import AuctionCase, AuctionItem, ClaimDistribution, AuctionParty, PropertyListing

# Admin 사이트 커스터마이징
admin.site.site_header = "BidHub 관리자"
admin.site.site_title = "BidHub Admin"
admin.site.index_title = "경매 매물 관리"

@admin.register(AuctionCase)
class AuctionCaseAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'case_name', 'court_name', 'filing_date', 'case_status')
    search_fields = ('case_number', 'case_name', 'court_name')
    list_filter = ('court_name', 'case_status', 'filing_date')
    ordering = ('-filing_date',)

@admin.register(AuctionItem)
class AuctionItemAdmin(admin.ModelAdmin):
    list_display = ('property_name', 'case_number', 'auction_date', 'current_min_price', 'item_status')
    search_fields = ('property_name', 'case_number__case_number', 'property_address')
    list_filter = ('item_status', 'property_type', 'auction_date')
    ordering = ('-auction_date',)

@admin.register(PropertyListing)
class PropertyListingAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'listing_type', 'location', 'final_result')
    search_fields = ('case_number__case_number', 'location')
    list_filter = ('listing_type', 'final_result')

@admin.register(ClaimDistribution)
class ClaimDistributionAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'location', 'claim_deadline')
    search_fields = ('case_number__case_number', 'location')
    list_filter = ('claim_deadline',)

@admin.register(AuctionParty)
class AuctionPartyAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'party_type', 'party_name', 'remarks')
    search_fields = ('case_number__case_number', 'party_name')
    list_filter = ('party_type',)
