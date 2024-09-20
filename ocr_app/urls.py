from django.urls import path
from .views import ocr_view
app_name = 'ocr_app'
urlpatterns = [
    path('upload/', ocr_view, name='ocr_upload'),
]
