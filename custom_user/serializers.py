from rest_framework import serializers

from custom_user.models import CustomUser,System


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model=CustomUser
        fields=['id','email','full_name','phone','gender','created_at']


class SystemSerializer(serializers.ModelSerializer):
    class Meta:
        model=System
        fields='__all__'


class KhaltiPaymentSerializer(serializers.Serializer):
    return_url = serializers.URLField(required=True)
    website_url = serializers.URLField(required=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)
    name = serializers.CharField(max_length=255, required=True)
    user_id = serializers.IntegerField(required=True)
   