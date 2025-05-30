from django.contrib import admin
from .models import AuctionCase, AuctionItem, ClaimDistribution, AuctionParty, PropertyListing

@admin.register(AuctionItem)
class AuctionItemAdmin(admin.ModelAdmin):
    list_display = ('item_number', 'case_number', 'item_purpose', 'item_status')
    search_fields = ('item_number', 'item_purpose')
    list_filter = ('item_status',)

@admin.register(AuctionCase)
class AuctionCaseAdmin(admin.ModelAdmin):
    list_display = ('case_number', 'case_name', 'court_name', 'filing_date')
    search_fields = ('case_number', 'case_name')
    list_filter = ('court_name',)

@admin.register(ClaimDistribution)
class ClaimDistributionAdmin(admin.ModelAdmin):
    list_display = ('id', 'case_number', 'claim_deadline')
    search_fields = ('case_number__case_number', 'location')

@admin.register(PropertyListing)
class PropertyListingAdmin(admin.ModelAdmin):
    list_display = ('id', 'case_number', 'listing_type', 'final_result')
    search_fields = ('case_number__case_number', 'location')
    list_filter = ('listing_type', 'final_result')

@admin.register(AuctionParty)
class AuctionPartyAdmin(admin.ModelAdmin):
    list_display = ('id', 'case_number', 'party_type', 'party_name')
    search_fields = ('case_number__case_number', 'party_name')
    list_filter = ('party_type',)
