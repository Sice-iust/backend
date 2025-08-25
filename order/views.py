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
from django.utils import timezone
from datetime import datetime
from django.utils.timezone import now
from django.db import transaction
from payment.views import ZarinpalPayment
from django.conf import settings
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from payment.models import ZarinpalTransaction
from django.db.models import Q
from .filters import OrderFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics
from users.permissions import IsAdminGroupUser
from users.ratetimes import *
from django.shortcuts import redirect
from django.http import HttpResponseRedirect


class SubmitOrderView(RateTimeBaseView, APIView):
    permission_classes = [IsAuthenticated]
    ratetime_class = [ThreePerMinuteLimit]
    serializer_class = FinalizeOrderSerializer

    def post(self, request):
        user = request.user
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )

        if not serializer.is_valid():
            return Response(serializer.errors, status=400)

        data = serializer.validated_data
        reciver, reciver_phone = self._get_receiver_info(user, data)

        location, delivery = self._get_location_and_delivery(data)
        if not location or not delivery:
            return Response({"error": "Invalid location or delivery slot."}, status=400)

        if self._is_delivery_slot_full(delivery):
            return Response({"error": "This delivery slot is full."}, status=400)

        discount = self._get_discount(data.get("discount_text", ""))

        cart_items = CartItem.objects.filter(user=user)
        stock_issue = self._check_stock(cart_items)
        if stock_issue:
            return Response({"error": stock_issue}, status=400)

        try:
            order = self._create_order(
                user,
                data,
                location,
                delivery,
                reciver,
                reciver_phone,
                discount,
                cart_items,
            )
        except Exception as e:
            return Response({"error": str(e)}, status=500)

        callback_url = self._build_callback_url(request, order.id)
        zarinpal = ZarinpalPayment(callback_url=callback_url)
        payment_response = zarinpal.request(
            user=user,
            amount=int(order.total_price),
            description=f"Order #{order.id} payment",
            merchant_id=settings.MERCHANT_ID,
        )

        if payment_response.status_code != 200:
            order.delete()
            return payment_response

        return Response(
            {"payment_url": payment_response.data["payment_url"]}, status=200
        )

    def _get_receiver_info(self, user, data):
        reciver = (
            data.get("reciver")
            if data.get("reciver") and data["reciver"] != "string"
            else user.username
        )
        reciver_phone = (
            data.get("reciver_phone")
            if data.get("reciver_phone") and data["reciver_phone"] != "string"
            else user.phonenumber
        )
        return reciver, reciver_phone

    def _get_location_and_delivery(self, data):
        try:
            location = Location.objects.get(id=data["location_id"])
            delivery = DeliverySlots.objects.get(id=data["deliver_time"])
            return location, delivery
        except (Location.DoesNotExist, DeliverySlots.DoesNotExist):
            return None, None

    def _is_delivery_slot_full(self, delivery):
        return delivery.current_fill >= delivery.max_orders

    def _get_discount(self, discount_text):
        discount_text = discount_text.strip()
        return (
            DiscountCart.objects.filter(text=discount_text).first()
            if discount_text
            else None
        )

    def _check_stock(self, cart_items):
        for item in cart_items:
            if item.product.stock < item.quantity:
                return f"Not enough stock for {item.product.name}."
        return None

    def _create_order(
        self,
        user,
        data,
        location,
        delivery,
        reciver,
        reciver_phone,
        discount,
        cart_items,
    ):
        with transaction.atomic():
            order = Order.objects.create(
                location=location,
                user=user,
                delivery=delivery,
                description=data["description"],
                total_price=data["total_price"],
                profit=data["profit"],
                status=1,
                discount=discount,
                pay_status="pending",
                reciver=reciver,
                reciver_phone=reciver_phone,
            )

            for item in cart_items:
                OrderItem.objects.create(
                    product=item.product,
                    order=order,
                    quantity=item.quantity,
                    product_discount=item.product.discount,
                )
                item.product.stock -= item.quantity
                item.product.save()
                item.delete()

            delivery.current_fill += 1
            delivery.save()
            return order

    def _build_callback_url(self, request, order_id):
        scheme = "https" if request.is_secure() else "http"
        return (
            f"{scheme}://{request.get_host()}/api/payment/verify/?order_id={order_id}"
        )


class ZarinpalVerifyView(RateTimeBaseView, APIView):
    ratetime_class = [ThreePerMinuteLimit]

    def get(self, request):
        user=request.user
        authority = request.GET.get("Authority")
        status_query = request.GET.get("Status")
        order_id = request.GET.get("order_id")

        try:
            transaction = ZarinpalTransaction.objects.get(authority=authority)
            order = Order.objects.get(id=order_id)
        except (ZarinpalTransaction.DoesNotExist, Order.DoesNotExist):
            return redirect(f"https://nanzi-amber.vercel.app/")
        zarinpal = ZarinpalPayment(callback_url="")  

        result = zarinpal.verify(
            status_query=status_query,
            authority=authority,
            merchant_id=settings.MERCHANT_ID,
            amount=transaction.amount,
        )
        if result.status_code == 200:
            order.pay_status = "paid"
            order.save()
            return redirect(f"https://nanzi-amber.vercel.app/ProfilePage")
        else:
            order.pay_status = "failed"
            order.status = 0
            order.save()
            return redirect(f"https://nanzi-amber.vercel.app/")


class OrderView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = MyOrderItemSerializer
    

    def get(self, request):
        user = request.user
        current_orders = OrderItem.objects.filter(order__user=user, order__status__lt=4,order__pay_status='paid')
        past_orders = OrderItem.objects.filter(
            order__user=user, order__status__gte=4, order__pay_status="paid"
        )
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
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    serializer_class = MyOrderItemSerializer

    def get(self, request):
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
        # this is a authentical problem IDOR
        order = get_object_or_404(Order, id=id, user=user)
        if order.pay_status!='paid':
            return Response({"this is failed."})
        invoices = OrderItem.objects.filter(order=order)
        serializer = OrderInvoiceSerializer(
            invoices, many=True, context={"request": request}
        )
        total_price = order.total_price or Decimal("0")
        discount = order.profit or Decimal("0")
        shipping_fee = order.delivery.shipping_fee or Decimal("0")

        return Response(
            {
                "payment": total_price - discount + shipping_fee,
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
        current_datetime = now()
        current_date = current_datetime.date()
        current_time = current_datetime.time()

        slots = DeliverySlots.objects.filter(
            delivery_date__gt=current_date
        ) | DeliverySlots.objects.filter(
            delivery_date=current_date, start_time__gt=current_time
        )

        grouped_data = self.group_slots_by_date(slots)
        serializer = DeliverySlotsByDaySerializer(grouped_data, many=True)
        return Response(serializer.data)


class AdminDeliverySlot(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    serializer_class = DeliverySlotSerializer

    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class SingleAdminDeliverySlot(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    serializer_class = DeliverySlotSerializer

    def put(self, request, pk):

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
        try:
            slot = DeliverySlots.objects.get(pk=pk)
            slot.delete()
            return Response({"message": "Slot deleted"})
        except DeliverySlots.DoesNotExist:
            return Response({"message": "Slot not found"}, status=404)


class AdminDeliveredOrder(APIView):
    serializer_class = MyOrderSerializer
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    def get(self, request):

        orders = Order.objects.filter(Q(status__gt=1) | Q(is_admin_canceled=True)|Q (is_archive=True))
        serializer = self.serializer_class(orders, many=True)
        return Response(serializer.data)

class AdminProcessing(APIView):
    serializer_class = MyOrderSerializer
    permission_classes = [IsAuthenticated, IsAdminGroupUser]

    def get(self, request):

        orders = Order.objects.filter(status=1,is_admin_canceled=False,is_archive=False,pay_status="paid")
        serializer = self.serializer_class(orders, many=True)
        return Response(serializer.data)

class AdminCancleView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    serializer_class = AdminCancelSerializer

    def post(self, request):

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            order = get_object_or_404(Order, id=data["order_id"])

            order.is_admin_canceled = True
            order.admin_reason = data["reason"]
            order.save()

            return Response({"message": "Order marked as admin-canceled successfully."})

        return Response(serializer.errors, status=400)


class AdminArchiveView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    serializer_class = AdminArchiveSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            data = serializer.validated_data
            order = get_object_or_404(Order, id=data["order_id"])
            order.is_archive = True
            order.save()

            return Response({"message": "Order marked as is_archive successfully."})

        return Response(serializer.errors, status=400)


class ChangeStatusView(RateTimeBaseView, APIView):
    permission_classes = [IsAuthenticated,IsAdminGroupUser]
    ratetime_class = [GetOnlyLimit]
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="status",
                description="Enter status number (1-4)",
                required=True,
                type=int,
            ),
        ]
    )
    def get(self, request, id):
        user=request.user
        status_param = request.query_params.get("status")

        if not status_param:
            return Response(
                {"error": "status parameter is required."},
                status=drf_status.HTTP_400_BAD_REQUEST,
            )

        try:
            new_status = int(status_param)
        except ValueError:
            return Response({"error": "status must be an integer."}, status=400)

        if new_status < 1 or new_status > 4:
            return Response({"error": "status must be between 1 and 4."}, status=400)

        try:
            order = Order.objects.get(id=id)
        except Order.DoesNotExist:
            return Response({"error": "Order not found."}, status=404)

        if order.status > new_status:
            return Response({"error": "Cannot downgrade order status."}, status=400)

        order.status = new_status
        order.save()

        return Response({"message": "Order status updated successfully."})


class OrderIdView(APIView):
    serializer_class = OrderIdSerializer
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    def get(self, request):

        orders = Order.objects.all()
        serializer = self.serializer_class(orders, many=True)
        return Response({"id": serializer.data})


class OrderListView(generics.ListAPIView):
    queryset = Order.objects.select_related("delivery", "user").all()
    serializer_class = MyOrderSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = OrderFilter
    permission_classes = [IsAuthenticated, IsAdminGroupUser]


class AdminOrderInvoiceView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    def get(self, request,id):
        
        order = get_object_or_404(Order, id=id)
        if order.pay_status != "paid":
            return Response({"this is failed."})
        invoices = OrderItem.objects.filter(order=order)
        serializer = OrderInvoiceSerializer(
            invoices, many=True, context={"request": request}
        )
        total_price = order.total_price or Decimal("0")
        discount = order.profit or Decimal("0")
        shipping_fee = order.delivery.shipping_fee or Decimal("0")

        return Response(
            {
                "payment": total_price - discount + shipping_fee,
                "shipping_fee": shipping_fee,
                "discount": discount,
                "items": serializer.data,
            }
        )
