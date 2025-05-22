from django import forms
from allauth.account.forms import SignupForm

class CustomSignupForm(SignupForm):
    name = forms.CharField(max_length=100, label='이름', required=True)
    id_number = forms.CharField(max_length=20, label='주민등록번호/법인번호', required=True)
    phone = forms.CharField(max_length=20, label='전화번호', required=True)
    address = forms.CharField(max_length=200, label='주소', required=True)
    # Add wallet_address if you want to collect it during signup too
    # wallet_address = forms.CharField(max_length=100, label='Metamask 지갑 주소', required=False)

    def save(self, request):
        # Call the parent class's save method to create and save the user
        user = super(CustomSignupForm, self).save(request)

        # Now that the user is saved, the signal should have created a Profile.
        # Update the profile with the extra data from the form.
        user.profile.name = self.cleaned_data['name']
        user.profile.id_number = self.cleaned_data['id_number']
        user.profile.phone = self.cleaned_data['phone']
        user.profile.address = self.cleaned_data['address']
        # if 'wallet_address' in self.cleaned_data:
        #     user.profile.wallet_address = self.cleaned_data['wallet_address']
        user.profile.save()

        return user 