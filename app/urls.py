from django.urls import path
from . import views
urlpatterns = [
    path('cases/', views.all_cases, name='all_cases'),
    path('item/<int:item_id>/', views.auction_detail, name='auction_detail'),
    path('auctions/', views.auction_list, name='auction_list'),
    path('properties/<int:item_id>/upload-image/', views.upload_property_image, name='upload_property_image'),
    path('properties/<int:item_id>/upload-images/', views.bulk_upload_images, name='bulk_upload_images'),
    path('api/refund/', views.dummy_view, name='refund'),
    path('pay_for_award/', views.pay_for_award_api),
    path('mark_additional_bid/', views.mark_additional_bid_api),
    path('withdraw/', views.withdraw_api),
    path('escrow_deposit/', views.escrow_deposit_api),
    path('confirm_bid/', views.confirm_bid_api),
    path('get_nonce/', views.get_nonce_api),
    path('inputbid/', views.inputbid_api),
    path('view_deposits/', views.view_deposits_api),
    path('get_balance/', views.get_balance_api),
    path('escrow_withdraw/', views.escrow_withdraw_api),
    path('putsec/', views.putsec_api),
    path('store_encrypted_bid/', views.store_encrypted_bid, name='store_encrypted_bid'),
    path("load_bid_history/", views.load_bid_history, name="load_bid_history")

]
