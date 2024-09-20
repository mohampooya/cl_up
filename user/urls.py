from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    AvailableTimesView, RegisterView, LoginView, QueueListCreateView, 
    NextPatientView, DoctorListBySpecialtyView, ReservationCreateView, 
    UserSpecialtyView, SpecialtyListView, CallPatientView, 
    DoctorRegistrationView, PatientRegistrationView, OCRAPIView, 
    ManualEntryAPIView, DoctorServiceListView, ServiceListCreateView, 
    ServiceDetailView
)

urlpatterns = [
    path('user/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('user/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('queue/', QueueListCreateView.as_view(), name='queue_list_create'),
    path('queue/next/<int:doctor_id>/', NextPatientView.as_view(), name='next_patient'),
    path('doctor/<int:doctor_id>/call/<str:call_type>/', CallPatientView.as_view(), name='call_patient'),
    path('doctors/register/', DoctorRegistrationView.as_view(), name='doctor_register'),
    path('specialties/', SpecialtyListView.as_view(), name='specialties_list'),
    path('specialties/<int:specialty_id>/doctors/', DoctorListBySpecialtyView.as_view(), name='doctors_by_specialty'),
    path('reservations/', ReservationCreateView.as_view(), name='create_reservation'),
    path('patient/register/', PatientRegistrationView.as_view(), name='patient_register'),
    path('api/ocr/', OCRAPIView.as_view(), name='api_ocr'),
    path('api/nationalidcards/', OCRAPIView.as_view(), name='nationalidcards'),
    path('api/available-times/<int:doctor_id>/', AvailableTimesView.as_view(), name='available-times'),
    path('api/manual-entry/', ManualEntryAPIView.as_view(), name='api_manual_entry'),
    path('doctor/services/', ServiceListCreateView.as_view(), name='service_list_create'),
    path('doctor/services/<int:pk>/', ServiceDetailView.as_view(), name='service_detail'),
    path('doctor/<int:doctor_id>/services/', DoctorServiceListView.as_view(), name='doctor_services'),
]
