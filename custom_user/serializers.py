from rest_framework import serializers

from custom_user.models import CustomUser

class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields=['email','full_name','phone']
        