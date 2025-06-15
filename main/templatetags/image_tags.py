from django import template
from main.utils.image_helper import get_property_main_image, get_case_main_image

register = template.Library()

@register.simple_tag
def get_auction_main_image(auction_item):
    """매물의 메인 이미지 URL 반환"""
    return get_property_main_image(auction_item)

@register.simple_tag
def get_case_image(case):
    """사건의 메인 이미지 URL 반환"""
    return get_case_main_image(case)

@register.simple_tag
def get_item_main_image(item):
    """AuctionItem의 메인 이미지 반환"""
    return get_property_main_image(item)

@register.filter
def has_image(auction_item):
    """매물에 이미지가 있는지 확인"""
    if not auction_item or not auction_item.item_image_url:
        return False
    return len(auction_item.item_image_url.strip()) == 6