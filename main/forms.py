from allauth.account.forms import SignupForm
from django import forms
from accounts.models import User  # accounts 앱의 User 모델 import

class CustomSignupForm(SignupForm):
    name = forms.CharField(max_length=100, required=True, label='이름')
    id_number = forms.CharField(max_length=14, required=True, label='주민등록번호')
    phone = forms.CharField(max_length=15, required=True, label='전화번호')
    address = forms.CharField(widget=forms.Textarea, required=True, label='주소')

    def save(self, request):
        user = super(CustomSignupForm, self).save(request)
        user.name = self.cleaned_data['name']
        user.id_number = self.cleaned_data['id_number']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        user.save()
        return user