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

class ReservationView(APIView):
    authentication_classes = [IsAuthenticated]
    serializer_class = ReservationSerializer

    def get(self, request):
        user = request.user
        reservs = BreadReservation.objects.filter(user=user).all()
        serializer = self.serializer_class(reservs, many=True)
        total_price_all = 0
        for item in reservs:
            base_price = item.product.price
            total_items =  item.quantity
            discount = item.product.discount or 0
            discounted_price = base_price * (1 - discount / 100)
            total_price_all += discounted_price * total_items

        return Response(
            {
                "reservations": serializer.data,
                "total_price_all": round(total_price_all, 2),
            }
        )

    def post(self, request):
        user = request.user
        data = request.data.copy()
        data["user"] = user.id  

        serializer = self.serializer_class(data=data, context={"request": request})
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": "Reservation created successfully",
                    "reservation": serializer.data,
                },
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminReservationView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ReservationSerializer

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
            discounted_price = base_price * (1 - discount / 100)
            total_price_all += discounted_price * total_items

        return Response(
            {
                "reservations": serializer.data,
                "total_price_all": round(total_price_all, 2),
            }
        )


class OrderReservesView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = OrderReservationSerializer

    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            if serializer.validated_data["is_paid"] is False:
                return Response({"message": "You should pay"}, status=400)

            reservations = BreadReservation.objects.filter(user=user, active=True)

            if not reservations.exists():
                return Response(
                    {"message": "No active reservations found."}, status=404
                )

            total_price = 0
            for res in reservations:
                base_price = res.product.price
                discount = res.product.discount or 0
                discounted_price = base_price * (1 - discount / 100)
                total_price += discounted_price * res.total_items

            location = reservations.first().location or "Unknown"
            delivery_time = reservations.first().next_delivery_date()

            order = Order.objects.create(
                user=user,
                location=location,
                delivery_time=delivery_time,
                total_price=round(total_price, 2),
            )

            for res in reservations:
                OrderItem.objects.create(
                    order=order,
                    product=res.product,
                    quantity=res.quantity,
                    box_type=res.box_type,
                    product_discount=res.product.discount or 0,
                )

            reservations.update(active=False)

            return Response(
                {
                    "message": "Order created from reservations successfully",
                    "order_id": order.id,
                    "total_price": order.total_price,
                },
                status=201,
            )

        return Response(serializer.errors, status=400)
