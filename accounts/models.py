from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('tasker', 'Tasker'),
    ]
    role = models.CharField(max_length=12, choices=ROLE_CHOICES, default='tasker')

    def is_admin(self):
        return self.role == 'admin'

    def is_tasker(self):
        return self.role == 'tasker'
