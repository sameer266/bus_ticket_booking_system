from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import random
from datetime import timedelta

class CustomUserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError("Phone number is required")
        
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")

        return self.create_user(phone=phone, password=password, **extra_fields)

# ======= Custom User Model ==============
class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_ROLES = (
        ("admin", "Admin User"),
        ("sub_admin", "Sub Admin"),
        ("bus_admin", "Bus Admin User"),
        ("customer", "Normal User"),
    )
    GENDER_CHOICE=(
        ("male","Male"),
        ("female","Female"),
        ("others","Others")
    )
    phone = models.CharField(max_length=15, unique=True) 
    email = models.EmailField(unique=True, null=True, blank=True,default="None" ) 
    full_name = models.CharField(max_length=255)   
    role = models.CharField(max_length=20, choices=USER_ROLES, default="customer")
    gender=models.CharField(max_length=50,choices=GENDER_CHOICE,null=True,blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at=models.DateField(auto_now_add=True,null=True)
    objects = CustomUserManager()

    USERNAME_FIELD = "phone"  
    REQUIRED_FIELDS = ["full_name"]  

    def __str__(self):
        return f"{self.full_name} - {self.role}"


class UserOtp(models.Model):
    user=models.ForeignKey(CustomUser,on_delete=models.CASCADE,limit_choices_to={'role':'customer'},null=True,blank=True)
    phone=models.CharField(max_length=15,null=True,blank=True)
    otp=models.CharField(max_length=6)
    created_at=models.DateTimeField(auto_now_add=True)
    temp_name=models.CharField(max_length=20,null=True,blank=True)
    
    # def is_expired(self):
    #     return  timezone.now()> self.created_at + timedelta(minutes=5)
    
    @staticmethod
    def generate_otp():
        while True:
            otp = str(random.randint(100000, 999999))
            if not UserOtp.objects.filter(otp=otp).exists():
                return otp
    
    def __str__(self):
        return f"{self.user} - {self.otp}"
