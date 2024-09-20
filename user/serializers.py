from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Patient, Doctor, Queue, Specialty, Reservation, NationalIDCard, Service
import datetime
import base64
import uuid
from django.core.files.base import ContentFile
import imghdr

# User serializer
User = get_user_model()

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'is_doctor')
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class ServicePublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ['service_name', 'service_image']

# Patient serializer
class PatientSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Patient
        fields = '__all__'

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer.create(UserSerializer(), validated_data=user_data)
        patient = Patient.objects.create(user=user, **validated_data)
        return patient

# Doctor serializer
class DoctorSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = Doctor
        fields = ['user', 'specialty']

    def create(self, validated_data):
        user_data = validated_data.pop('user')
        user = UserSerializer.create(UserSerializer(), validated_data=user_data)
        doctor = Doctor.objects.create(user=user, **validated_data)
        return doctor

# Service serializer
class ServiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = '__all__'

# Specialty serializer
class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = '__all__'

# Queue serializer
class QueueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Queue
        fields = '__all__'

# Reservation serializer
class ReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reservation
        fields = ['id', 'patient', 'doctor', 'reservation_time']

# National ID Card serializer
class NationalIDCardSerializer(serializers.ModelSerializer):
    class Meta:
        model = NationalIDCard
        fields = ['national_id', 'first_name', 'last_name', 'father_name', 'birth_date']

    def validate_birth_date(self, value):
        if value > datetime.date.today():
            raise serializers.ValidationError("Birth date cannot be in the future.")
        return value

# Base64 Image Field serializer
class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and 'data:' in data and ';base64,' in data:
            header, data = data.split(';base64,')
        try:
            decoded_file = base64.b64decode(data)
        except (TypeError, base64.binascii.Error):
            self.fail('invalid_image')
        
        file_name = str(uuid.uuid4())[:12]
        file_extension = self.get_file_extension(file_name, decoded_file)
        complete_file_name = f"{file_name}.{file_extension}"
        return ContentFile(decoded_file, name=complete_file_name)

    def get_file_extension(self, file_name, decoded_file):
        extension = imghdr.what(file_name, decoded_file)
        return "jpg" if extension == "jpeg" else extension

# Image upload serializer
class ImageUploadSerializer(serializers.Serializer):
    image = Base64ImageField(max_length=None, use_url=True)
