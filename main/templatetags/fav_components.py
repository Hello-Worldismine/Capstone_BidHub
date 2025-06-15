from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.inclusion_tag('main/components/fav_container.html')
def render_fav_container(items, item_type, empty_message='검색 결과가 없습니다.'):
    """기존 컴포넌트"""
    return {
        'items': items,
        'item_type': item_type,
        'empty_message': empty_message,
    }

@register.inclusion_tag('main/components/fav_container_with_remove.html')
def render_fav_container_with_remove(items, item_type, empty_message='즐겨찾기한 매물이 없습니다.'):
    """즐겨찾기 페이지용 컴포넌트 (제거 기능 포함)"""
    return {
        'items': items,
        'item_type': item_type,
        'empty_message': empty_message,
    }

@register.inclusion_tag('main/components/property_type_badge.html')
def render_property_badge(property_type):
    """물건 종류 배지 렌더링"""
    return {'property_type': property_type}

@register.inclusion_tag('main/components/price_display.html')  
def render_price(amount):
    """가격 표시 렌더링"""
    return {'amount': amount}

@register.simple_tag
def get_item_case_number(item, item_type):
    """아이템 타입에 따라 사건번호 반환"""
    if item_type == 'auction_item':
        return item.case_number.case_number if hasattr(item, 'case_number') else ''
    else:
        return item.case_number if hasattr(item, 'case_number') else ''