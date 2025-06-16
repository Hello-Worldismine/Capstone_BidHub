from django import forms
from django.core.files.storage import default_storage
import os
import uuid
from django.conf import settings

class ImageUploadForm(forms.Form):
    """이미지 업로드를 위한 폼"""
    images = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True, 'accept': 'image/*'}),
        label='이미지 파일들',
        help_text='여러 이미지를 선택할 수 있습니다. (JPG, PNG 등)',
        required=True
    )
    
    def clean_images(self):
        images = self.files.getlist('images')
        if not images:
            raise forms.ValidationError('최소 1개의 이미지를 선택해주세요.')
        
        # 이미지 파일 검증
        for image in images:
            if not image.content_type.startswith('image/'):
                raise forms.ValidationError(f'{image.name}은(는) 이미지 파일이 아닙니다.')
        
        return images
    
    def save_images(self):
        """이미지들을 저장하고 새 폴더 번호를 반환"""
        images = self.files.getlist('images')
        
        # 새 폴더 번호 생성 (기존 폴더들보다 큰 숫자 사용)
        itemimages_path = os.path.join(settings.BASE_DIR, 'main', 'static', 'img', 'itemimages')
        
        # 기존 폴더 번호들 찾기
        existing_folders = []
        if os.path.exists(itemimages_path):
            for folder in os.listdir(itemimages_path):
                if folder.isdigit():
                    existing_folders.append(int(folder))
        
        # 새 폴더 번호 생성
        new_folder_number = max(existing_folders) + 1 if existing_folders else 1000000
        new_folder_path = os.path.join(itemimages_path, str(new_folder_number))
        
        # 폴더 생성
        os.makedirs(new_folder_path, exist_ok=True)
        
        # 이미지들 저장
        for i, image in enumerate(images, 1):
            # 파일 확장자 얻기
            file_extension = os.path.splitext(image.name)[1].lower()
            if not file_extension:
                file_extension = '.jpg'
            
            # 새 파일명 생성 (기존 패턴에 맞춤)
            new_filename = f'img_{i}_wm{file_extension}'
            file_path = os.path.join(new_folder_path, new_filename)
            
            # 파일 저장
            with open(file_path, 'wb+') as destination:
                for chunk in image.chunks():
                    destination.write(chunk)
        
        return str(new_folder_number)
