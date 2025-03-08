from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_ROLES = (
        ("admin", "Admin User"),
        ('sub_admin','Sub Admin'),
        ("bus_admin", "Bus Admin User"),
        ("customer", "Normal User"),
    )

    email = models.EmailField(unique=True, null=False)
    full_name = models.CharField(max_length=255, null=False, blank=False)
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)  # Increased length for international numbers
    role = models.CharField(max_length=20, choices=USER_ROLES, default="customer")
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["full_name", "role"]

    def __str__(self):
        return f"{self.full_name} - {self.role}"
