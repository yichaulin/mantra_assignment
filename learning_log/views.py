from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Record
from .serializers import RecordSerializer
from django.db import IntegrityError, transaction

# Create your views here.

class RecordCreateView(APIView):
    def post(self, request):
        user_id = request.headers.get("X-USER-ID")

        data = request.data.copy()
        data["user_id"] = user_id

        record = RecordSerializer(data=data)
        record.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                record.save()
        except IntegrityError:
            return Response(status=status.HTTP_201_CREATED)
        
        return Response(status=status.HTTP_201_CREATED)