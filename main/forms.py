from allauth.account.forms import SignupForm
from django import forms
from accounts.models import User
from accounts.models import Profile  # Profile 모델 import 추가

class CustomSignupForm(SignupForm):
    name = forms.CharField(max_length=100, required=True, label='이름')
    id_number = forms.CharField(max_length=14, required=True, label='주민등록번호')
    phone = forms.CharField(max_length=15, required=True, label='전화번호')
    address = forms.CharField(widget=forms.Textarea, required=True, label='주소')

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        
        # User 모델의 추가 필드 저장
        user.name = self.cleaned_data['name']
        user.id_number = self.cleaned_data['id_number']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        user.save()
        
        # Profile 모델이 존재한다면 Profile에도 저장
        try:
            profile, created = Profile.objects.get_or_create(user=user)
            profile.name = self.cleaned_data['name']
            profile.id_number = self.cleaned_data['id_number']
            profile.phone = self.cleaned_data['phone']
            profile.address = self.cleaned_data['address']
            profile.save()
        except:
            # Profile 모델이 없거나 오류가 있는 경우 무시
            pass
            
        return user