import os
from django.conf import settings

def get_property_images(auction_item):
    """AuctionItem 객체로부터 이미지 경로들 반환 (static 경로 사용)"""
    
    if not auction_item or not auction_item.item_image_url:
        print("❌ auction_item 또는 item_image_url이 없음")
        return []
    
    folder_code = auction_item.item_image_url.strip()
    print(f"🔍 폴더 코드: {folder_code}")
    
    if len(folder_code) != 6 or not folder_code.isdigit():
        print(f"❌ 잘못된 폴더 코드: {folder_code}")
        return []
    
    # static 폴더 경로 확인
    static_path = os.path.join(settings.BASE_DIR, 'main', 'static', 'img', 'itemimages', folder_code)
    
    print(f"📁 이미지 폴더 경로: {static_path}")
    print(f"📁 폴더 존재 여부: {os.path.exists(static_path)}")
    
    if not os.path.exists(static_path):
        print(f"❌ 폴더가 존재하지 않음: {static_path}")
        return []
    
    # 이미지 파일들 가져오기
    try:
        all_files = os.listdir(static_path)
        print(f"📄 폴더 내 모든 파일: {all_files}")
        
        image_files = [f for f in all_files 
                      if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        
        print(f"🖼️ 이미지 파일들: {image_files}")
    except Exception as e:
        print(f"❌ 파일 목록 조회 오류: {e}")
        return []
    
    # 자연 정렬
    def natural_sort_key(filename):
        import re
        numbers = re.findall(r'\d+', filename)
        return [int(num) for num in numbers] if numbers else [0]
    
    image_files.sort(key=natural_sort_key)
    
    # static URL 경로로 변환
    image_urls = [f"/static/img/itemimages/{folder_code}/{img}" for img in image_files]
    
    print(f"🌐 생성된 URL들: {image_urls}")
    
    return image_urls

def get_property_main_image(auction_item):
    """매물의 대표 이미지 하나만 반환"""
    images = get_property_images(auction_item)
    return images[0] if images else None

def get_case_main_image(case):
    """사건의 대표 이미지 하나만 반환 (첫 번째 매물의 첫 번째 이미지)"""
    try:
        from app.models import AuctionItem
        
        # 해당 사건의 첫 번째 매물 가져오기 (이미지가 있는 것 우선)
        auction_item = AuctionItem.objects.filter(
            case_number=case
        ).exclude(
            item_image_url__isnull=True
        ).exclude(
            item_image_url=''
        ).first()
        
        if auction_item:
            return get_property_main_image(auction_item)
        
        # 이미지가 없다면 첫 번째 매물이라도 반환
        auction_item = AuctionItem.objects.filter(case_number=case).first()
        if auction_item:
            return get_property_main_image(auction_item)
            
        return None
    except Exception as e:
        print(f"이미지 조회 오류: {e}")
        return None