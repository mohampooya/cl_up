from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .user.serializers import ImageUploadSerializer
import pytesseract
from PIL import Image
from django.core.files.storage import default_storage

class OCRAPIView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = ImageUploadSerializer(data=request.data)
        if serializer.is_valid():
            image = serializer.validated_data['image']
            file_name = default_storage.save(image.name, image)
            file_path = default_storage.path(file_name)
            
            pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img, lang='fas')
            
            default_storage.delete(file_name)
            
            return Response({'text': text}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

