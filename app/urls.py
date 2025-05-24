from django.urls import path
from . import views

urlpatterns = [
    path('cases/', views.all_cases, name='all_cases'),
    path('item/<int:item_id>/', views.auction_detail, name='auction_detail'),
    path('auctions/', views.auction_list, name='auction_list'),
    path('properties/<int:item_id>/upload-image/', views.upload_property_image, name='upload_property_image'),
    path('properties/<int:item_id>/upload-images/', views.bulk_upload_images, name='bulk_upload_images'),
]
