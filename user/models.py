from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
import uuid
import datetime


class NationalIDCard(models.Model):
    national_id = models.CharField(max_length=10, unique=True)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    birth_date = models.DateField()

    def __str__(self):
        return f"{self.last_name} {self.first_name}"

    def full_details(self):
        return (f"ID: {self.national_id}, First Name: {self.first_name}, "
                f"Last Name: {self.last_name}, Father's Name: {self.father_name}, "
                f"Birth Date: {self.birth_date.strftime('%Y-%m-%d')}")


class Specialty(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(default='')  # Ensure this line is present

    def __str__(self):
        return self.name


class User(AbstractUser):
    is_doctor = models.BooleanField(default=False)

    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )

    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )


class Patient(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    national_code = models.CharField(max_length=10, unique=True)
    date_of_birth = models.DateField()
    type_of_insurance = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Doctor(models.Model):
    name = models.CharField(max_length=100, default='Unknown')
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    specialty = models.ForeignKey(Specialty, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.user.username  # Use the User's username or full name


class Reservation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    date = models.DateField(default=datetime.date.today)
    time = models.TimeField(default=datetime.time(9, 0))
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    reservation_time = models.DateTimeField(auto_now_add=True)  # Automatically set the reservation time

    class Meta:
        unique_together = ('doctor', 'date', 'time')

    def __str__(self):
        return f"Reservation for {self.patient.username} with Dr. {self.doctor.user.username} on {self.date} at {self.time}"


class Queue(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE)
    position = models.PositiveIntegerField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Patient {self.patient} is in position {self.position} for Dr. {self.doctor}"


class Service(models.Model):
    doctor = models.ForeignKey('Doctor', on_delete=models.CASCADE, related_name='services')
    service_code = models.CharField(max_length=20, unique=True)
    service_name = models.CharField(max_length=100)
    service_price = models.DecimalField(max_digits=10, decimal_places=2)
    insurance_price = models.DecimalField(max_digits=10, decimal_places=2)
    service_image = models.ImageField(upload_to='services/', null=True, blank=True)

    def __str__(self):
        return self.service_name
