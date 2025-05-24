from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)

    class Meta:
        model = User
        fields = ('username', 'password', 'password2', 'email', 'first_name', 'last_name', 'gender', 'birth_date', 'region', 'address', 'phone', 'mobile', 'terms_conditions')
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        if data['password'] != data.pop('password2'):
            raise serializers.ValidationError("Passwords must match.")
        validate_password(data['password'])
        return data

    def create(self, validated_data):
        user = User.objects.create(
            username=validated_data['username'],
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            gender=validated_data['gender'],
            birth_date=validated_data['birth_date'],
            region=validated_data['region'],
            address=validated_data['address'],
            phone=validated_data['phone'],
            mobile=validated_data['mobile'],
            terms_conditions=validated_data['terms_conditions']
        )
        user.set_password(validated_data['password'])
        user.save()
        return user