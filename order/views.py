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
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            data = serializer.validated_data
            discount = DiscountCart.objects.filter(
                text=data.get("discount_text")
            ).first()

            cart_items = CartItem.objects.filter(user=user).all()

            for item in cart_items:
                if not self._has_sufficient_stock(item):
                    return Response(
                        {"error": f"Not enough stock for {item.product.name}."},
                        status=400,
                    )

            order = serializer.save()

            for item in cart_items:
                p_dis = item.product.discount
                OrderItem.objects.create(
                    product=item.product,
                    order=order,
                    quantity=item.quantity,
                    product_discount=p_dis,
                )
                item.product.stock -= item.quantity
                item.product.save()
                item.delete()

            return Response({"message": "Order submitted successfully!"})

        return Response(serializer.errors, status=400)

    def _has_sufficient_stock(self, item):
        return item.product.stock >= item.quantity


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


from decimal import Decimal


class OrderInvoiceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        user = request.user
        order = get_object_or_404(Order, id=id, user=user)
        invoices = OrderItem.objects.filter(order=order)
        serializer = OrderInvoiceSerializer(
            invoices, many=True, context={"request": request}
        )
        total_price = order.total_price or Decimal("0")
        discount = order.profit or Decimal("0")
        shipping_fee = order.delivery.shipping_fee or Decimal("0")

        return Response(
            {
                "payment": total_price + discount - shipping_fee,
                "shipping_fee": shipping_fee,
                "discount": discount,
                "items": serializer.data,
            }
        )

class DeliverSlotView(APIView):
    serializer_class = DeliverySlotsByDaySerializer

    def group_slots_by_date(self,slots):
        from collections import defaultdict

        grouped = defaultdict(list)
        for slot in slots:
            grouped[slot.delivery_date].append(slot)

        return [{"delivery_date": date, "slots": group} for date, group in grouped.items()]

    def get(self, request):
        slots = DeliverySlots.objects.all()
        grouped_data = self.group_slots_by_date(slots)
        serializer = DeliverySlotsByDaySerializer(grouped_data, many=True)
        return Response(serializer.data)


class AdminDeliverySlot(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliverySlotSerializer

    def check_admin(self, request):
        admin_group = Group.objects.get(name="Admin")
        return admin_group in request.user.groups.all()

    def post(self, request):
        if not self.check_admin(request):
            return Response({"message": "Permission denied"}, status=403)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class SingleAdminDeliverySlot(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = DeliverySlotSerializer

    def check_admin(self, request):
        admin_group = Group.objects.get(name="Admin")
        return admin_group in request.user.groups.all()

    def put(self, request, pk):
        if not self.check_admin(request):
            return Response({"message": "Permission denied"}, status=403)

        try:
            slot = DeliverySlots.objects.get(pk=pk)
        except DeliverySlots.DoesNotExist:
            return Response({"message": "Slot not found"}, status=404)

        serializer = self.serializer_class(slot, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    def delete(self, request, pk):
        if not self.check_admin(request):
            return Response({"message": "Permission denied"}, status=403)

        try:
            slot = DeliverySlots.objects.get(pk=pk)
            slot.delete()
            return Response({"message": "Slot deleted"})
        except DeliverySlots.DoesNotExist:
            return Response({"message": "Slot not found"}, status=404)
