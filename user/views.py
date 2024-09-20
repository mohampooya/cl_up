from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.shortcuts import get_object_or_404
from django.core.files.storage import default_storage
from django.forms.models import model_to_dict
from django.views import View
from django.http import JsonResponse
from io import BytesIO
from PIL import Image
import base64
import os
import pytesseract
import re
import datetime

from .models import Patient, Doctor, Queue, NationalIDCard, Specialty, Service, Reservation
from .serializers import (
    UserSerializer, PatientSerializer, DoctorSerializer, QueueSerializer, 
    ReservationSerializer, SpecialtySerializer, NationalIDCardSerializer, 
    ServiceSerializer, ServicePublicSerializer, ImageUploadSerializer
)


class AvailableTimesView(APIView):
    def get(self, request, doctor_id):
        try:
            doctor = Doctor.objects.get(pk=doctor_id)
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)

        date_str = request.GET.get('date')
        if not date_str:
            return Response({'error': 'No date provided'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({'error': 'Invalid date format'}, status=status.HTTP_400_BAD_REQUEST)

        if date.weekday() == 4:  # Check if the date is a Friday
            return Response({'error': 'Reservations are not available on Fridays'}, status=status.HTTP_400_BAD_REQUEST)

        default_times = ["9:00", "10:00", "11:00", "12:00", "16:00", "17:00", "18:00", "19:00"]
        booked_times = list(Reservation.objects.filter(doctor=doctor, date=date).values_list('time', flat=True))
        available_times = [time for time in default_times if time not in booked_times]

        return Response({'available_times': available_times}, status=status.HTTP_200_OK)




class OCRAPIView(APIView):
    def post(self, request, *args, **kwargs):
        data = request.data.get('image')
        if not data:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        # Decode the base64 image
        image_data = base64.b64decode(data.split(",")[1])
        image_file = BytesIO(image_data)
        image = Image.open(image_file)
        
        # Use pytesseract to extract text
        text = pytesseract.image_to_string(image, lang='fas')

        # Clean and split the text by lines
        lines = re.split(r'\n+', text.strip())

        # Initialize all fields with default or empty values
        card_info = {
            "national_id": lines[0] if len(lines) > 0 else "Unknown",
            "first_name": lines[1] if len(lines) > 1 else "Unknown",
            "last_name": lines[2] if len(lines) > 2 else "Unknown",
            "father_name": lines[3] if len(lines) > 3 else "Unknown",
            "birth_date": lines[4] if len(lines) > 4 else "Unknown"
        }

        # Send extracted data back for user confirmation
        return Response({"data": card_info}, status=status.HTTP_200_OK)


class ManualEntryAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = NationalIDCardSerializer(data=request.data)
        if serializer.is_valid():
            # Here, you would typically save the data to a database
            return Response({"data": serializer.validated_data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


VOICE_PATH = 'voice/PS1505-iww234963dgd-www/'

class CallPatientView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, doctor_id, call_type, *args, **kwargs):
        doctor = get_object_or_404(Doctor, pk=doctor_id)
        queue = Queue.objects.filter(doctor=doctor).order_by('position')

        if call_type == 'initial':
            patient_queue = queue.first()
        elif call_type == 'next':
            patient_queue = queue.first()
            if patient_queue:
                patient_queue.delete()
        elif call_type == 'last':
            patient_queue = queue.last()
        else:
            return Response({'error': 'Invalid call type'}, status=status.HTTP_400_BAD_REQUEST)

        if not patient_queue:
            return Response({'message': 'No patients in queue'}, status=status.HTTP_200_OK)

        queue_number = patient_queue.position
        voice_files = get_voice_files(queue_number)
        
        return Response({'voice_files': voice_files}, status=status.HTTP_200_OK)

def get_voice_files(number):
    if number <= 20:
        return [f'{VOICE_PATH}{number}.mp3']
    else:
        tens = (number // 10) * 10
        units = number % 10
        return [f'{VOICE_PATH}{tens}o.mp3', f'{VOICE_PATH}{units}.mp3']

class RegisterView(generics.CreateAPIView):
    queryset = Patient.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        if user.is_doctor:
            Doctor.objects.create(user=user)
        else:
            Patient.objects.create(user=user)

class LoginView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, *args, **kwargs):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({'token': token.key}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid Credentials'}, status=status.HTTP_400_BAD_REQUEST)

class QueueListCreateView(generics.ListCreateAPIView):
    queryset = Queue.objects.all()
    serializer_class = QueueSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save()

class NextPatientView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, doctor_id, *args, **kwargs):
        try:
            doctor = Doctor.objects.get(pk=doctor_id)
            next_patient = Queue.objects.filter(doctor=doctor).order_by('position').first()
            if next_patient:
                next_patient.delete()
                return Response({'message': f'Next patient: {next_patient.patient.user.username}'}, status=status.HTTP_200_OK)
            return Response({'message': 'No patients in queue'}, status=status.HTTP_200_OK)
        except Doctor.DoesNotExist:
            return Response({'error': 'Doctor not found'}, status=status.HTTP_404_NOT_FOUND)

class DoctorRegistrationView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        user_serializer = UserSerializer(data=request.data.get('user'))
        if user_serializer.is_valid():
            user_instance = user_serializer.save()
            doctor_data = {
                'user': user_instance.pk,
                'specialty': request.data.get('specialty')
            }
            doctor_serializer = DoctorSerializer(data=doctor_data)
            if doctor_serializer.is_valid():
                doctor_serializer.save()
                return Response(doctor_serializer.data, status=status.HTTP_201_CREATED)
            user_instance.delete()  # Delete user if doctor creation fails
            return Response(doctor_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class SpecialtyListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            specialties = Specialty.objects.all()
            serializer = SpecialtySerializer(specialties, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(str(e), status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DoctorListBySpecialtyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, specialty_id):
        doctors = Doctor.objects.filter(specialty=specialty_id)
        serializer = DoctorSerializer(doctors, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ReservationCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ReservationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserSpecialtyView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = UserSpecialtySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Specialty selected successfully"}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PatientRegistrationView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        serializer = PatientSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"detail": "Patient registered successfully"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ServiceListCreateView(generics.ListCreateAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        doctor = self.request.user.doctor
        return Service.objects.filter(doctor=doctor)

    def perform_create(self, serializer):
        serializer.save(doctor=self.request.user.doctor)

class ServiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        doctor = self.request.user.doctor
        return Service.objects.filter(doctor=doctor)

class DoctorServiceListView(generics.ListAPIView):
    serializer_class = ServicePublicSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        doctor_id = self.kwargs.get('doctor_id')
        return Service.objects.filter(doctor__id=doctor_id)
