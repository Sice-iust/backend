from django.shortcuts import render
from .models import *
from .serializers import *
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser
from django.http import Http404
from django.contrib.auth.models import Group
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from drf_spectacular.utils import extend_schema, OpenApiParameter
from order.models import Order
from rest_framework import status
from users.models import Location


class ReservationView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReservationProductSerializer

    def get(self, request):
        user = request.user
        reservs = ReserveItem.objects.filter(user=user).all()
        serializer = self.serializer_class(reservs, many=True)
        total_price_all = 0
        for item in reservs:
            base_price = item.product.price
            total_items =  item.quantity
            discount = item.product.discount or 0
            discount_rate = Decimal(1) - (Decimal(discount) / Decimal(100))
            discounted_price = base_price * discount_rate
            total_price_all += discounted_price * total_items

        return Response(
            {
                "reservations": serializer.data,
                "total_price_all": total_price_all,
            }
        )


class AdminReservationView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReservationProductSerializer

    def get(self, request):
        if not request.user.groups.filter(name="Admin").exists():
            return Response({"message": "Permission denied"}, status=403)
        reservs = BreadReservation.objects.all()
        serializer = self.serializer_class(
            reservs, many=True, context={"request": request}
        )
        total_price_all = 0
        for item in reservs:
            base_price = item.product.price
            total_items =  item.quantity
            discount = item.product.discount or 0
            discounted_price = Decimal(base_price * (1 - discount / 100))
            total_price_all += discounted_price * total_items

        return Response(
            {
                "reservations": serializer.data,
                "total_price_all": total_price_all,
            }
        )

class SubmitReserveView(APIView):
    permission_classes=[IsAuthenticated]
    serializer_class=ReservationSerializer
    def post(self,request):
        user=request.user
        serializer=self.serializer_class(data=request.data)
        if serializer.is_valid():
            location=Locations.objects.get(id=serializer.validated_data['location_id'])
            delivery=DeliverSlots.object.get(id=serializer.validated_data['delivery_id'])
            if delivery.current_fill >= delivery.max_orders:
                        return Response({"error": "This delivery slot is full."}, status=400)
            discount_text = data.get("discount_text", "").strip()
            discount = (
                DiscountCart.objects.filter(text=discount_text).first()
                if discount_text
                else None
            )
            reserve = BreadReservation.objects.create(
                location=location,
                delivery=delivery,
                user=user,
                is_active=False,
                auto_pay=False,
                period=serializer.validated_data['period']
            )
            cart_items = CartItem.objects.filter(user=user).all()

            for item in cart_items:
                if not self._has_sufficient_stock(item):
                    return Response(
                        {"error": f"Not enough stock for {item.product.name}."},
                        status=400,
                    )

            for item in cart_items:
                p_dis = item.product.discount
                ReserveItem.objects.create(
                    product=item.product,
                    reserve=reserve,
                    quantity=item.quantity,
                )

                item.delete()
        return Response("something went wrong.")

