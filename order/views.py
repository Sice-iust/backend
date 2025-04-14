from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.http import Http404
from django.contrib.auth.models import Group
from .models import *
from django.utils import timezone
from datetime import timedelta
from django.http import Http404
from django.shortcuts import get_object_or_404


class DiscountCartView(APIView):
    serializer_class = DiscountCartSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        now = timezone.now()
        two_days_later = now + timedelta(days=2)
        expired_discounts = DiscountCart.objects.filter(user=user, expired_time__lt=now)
        expiring_soon = DiscountCart.objects.filter(
            user=user, expired_time__gte=now, expired_time__lte=two_days_later
        )
        active_discounts = DiscountCart.objects.filter(
            user=user, expired_time__gt=two_days_later
        )

        return Response(
            {
                "expired": DiscountCartSerializer(expired_discounts, many=True).data,
                "expiring_soon": DiscountCartSerializer(expiring_soon, many=True).data,
                "active": DiscountCartSerializer(
                    active_discounts, many=True
                ).data,
            }
        )
    def post(self,request):
        admin_group = Group.objects.get(name="Admin")
        if not admin_group in request.user.groups.all():
            return Response({"message": "Permission denied"}, status=403)
        serializer=self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response("you make a discount")
        return Response(serializer.errors, status=400)


class SingleDiscountCartView(APIView):
    serializer_class = DiscountCartSerializer
    permission_classes = [IsAuthenticated]
    def put(self,request,id):
        admin_group = Group.objects.get(name="Admin")
        if not admin_group in request.user.groups.all():
            return Response({"message": "Permission denied"}, status=403)
        discount = get_object_or_404(DiscountCart, id=id)
        serializer = self.serializer_class(discount, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Discount updated successfully", "data": serializer.data},
                status=200,
            )
        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        admin_group = Group.objects.get(name="Admin")
        if admin_group not in request.user.groups.all():
            return Response({"message": "Permission denied"}, status=403)
        discount = get_object_or_404(DiscountCart, id=id)
        discount.delete()
        return Response({"message": "Discount deleted successfully"}, status=200)
