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


class MyDiscountView(APIView):
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


class AdminDiscountView(APIView):
    serializer_class = DiscountCartSerializer

    permission_classes = [IsAuthenticated]

    def get(self, request):

        admin_group = Group.objects.get(name="Admin")
        if admin_group not in request.user.groups.all():
            return Response({"message": "Permission denied"}, status=403)
        discounts = DiscountCart.objects.all()

        serializer = self.serializer_class(discounts, many=True)

        return Response({"discounts": serializer.data})

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


class SubmitOrderView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = FinalizeOrderSerializer

    def post(self, request):
        user = request.user
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            discount = DiscountCart.objects.filter(text=data.get("discount")).first()

            cart_items = CartItem.objects.filter(user=user).all()

            for item in cart_items:
                if not self._has_enough_stock(item):
                    return Response(
                        {
                            "error": f"Not enough stock for product '{item.product.name}' (box type {item.box_type})"
                        },
                        status=400,
                    )
            order = Order.objects.create(
                user=user,
                distination=data["distination"],
                delivery_time=data["deliver_time"],
                discription=data.get("discription", ""),
                status=1,
                discount=discount,
                total_price=data["total_price"],
                shipping_fee=data["shipping_fee"],
            )

            for item in cart_items:
                p_dis = item.product.discount
                OrderItem.objects.create(
                    product=item.product,
                    order=order,
                    quantity=item.quantity,
                    product_discount=p_dis,
                    box_type=item.box_type,
                )

                self._reduce_stock(item)
                item.delete()

            return Response({"message": "Order submitted successfully!"})

        return Response(serializer.errors, status=400)

    def _has_enough_stock(self, item):
        product = item.product
        quantity = item.quantity
        box_type = item.box_type

        if box_type == 2:
            return quantity <= product.stock_1
        if box_type == 4:
            return quantity <= product.stock_4
        if box_type == 6:
            return quantity <= product.stock_6
        if box_type == 8:
            return quantity <= product.stock_8
        return False

    def _reduce_stock(self, item):
        product = item.product
        quantity = item.quantity
        box_type = item.box_type

        if box_type == 1:
            product.stock_1 -= quantity
        elif box_type in [2, 3, 4]:
            product.stock_2 -= quantity

        product.save()


class OrderView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MyOrderItemSerializer

    def get(self, request):
        user = request.user
        current_orders = OrderItem.objects.filter(order__user=user, order__status__lt=4)
        past_orders = OrderItem.objects.filter(order__user=user, order__status__gte=4)
        now_serializer = self.serializer_class(
            current_orders, many=True, context={"request": request}
        ).data
        past_serializer = self.serializer_class(
            past_orders, many=True, context={"request": request}
        ).data
        return Response(
            {"current_orders": now_serializer, "past_orders": past_serializer}
        )


class AllOrderView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MyOrderItemSerializer

    def get(self, request):
        admin_group = Group.objects.get(name="Admin")
        if not admin_group in request.user.groups.all():
            return Response({"message": "Permission denied"}, status=403)
        user = request.user
        current_orders = OrderItem.objects.filter(order__status__lt=4)
        past_orders = OrderItem.objects.filter(order__status__gte=4)
        now_serializer = self.serializer_class(
            current_orders, many=True, context={"request": request}
        )
        past_serializer = self.serializer_class(
            past_orders, many=True, context={"request": request}
        )
        return Response(
            {"current_orders": now_serializer.data, "past_orders": past_serializer.data}
        )
