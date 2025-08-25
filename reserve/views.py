# from django.shortcuts import render
# from .models import *
# from .serializers import *
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAdminUser
# from django.http import Http404
# from django.contrib.auth.models import Group
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
# from drf_spectacular.utils import extend_schema, OpenApiParameter
# from order.models import *
# from rest_framework import status
# from users.models import Location
# from django.shortcuts import render
# from .models import *
# from .serializers import *
# from rest_framework.permissions import IsAuthenticated
# from rest_framework.views import APIView
# from rest_framework.response import Response
# from rest_framework.permissions import IsAdminUser
# from django.http import Http404
# from django.contrib.auth.models import Group
# from .models import *
# from django.utils import timezone
# from datetime import timedelta
# from django.http import Http404
# from django.shortcuts import get_object_or_404
# from django.utils import timezone
# from datetime import datetime
# from django.utils.timezone import now
# from django.db import transaction
# from payment.views import ZarinpalPayment
# from django.conf import settings
# from drf_yasg.utils import swagger_auto_schema
# from drf_yasg import openapi
# from drf_spectacular.utils import extend_schema, OpenApiParameter
# from rest_framework import status
# from payment.models import ZarinpalTransaction
# from django.db.models import Q
# from django_filters.rest_framework import DjangoFilterBackend
# from rest_framework import generics
# from users.permissions import IsAdminGroupUser
# from users.ratetimes import *
# from django.shortcuts import redirect
# from django.http import HttpResponseRedirect

# class ReservationView(APIView):
#     permission_classes = [IsAuthenticated]
#     serializer_class = ReservationSerializer

#     def get(self, request):
#         user = request.user
#         reservs = Reservation.objects.get(user=user).all()
#         serializer = self.serializer_class(reservs, many=True)
#         total_price_all = 0
#         for item in reservs:
#             base_price = item.product.price
#             total_items =  item.quantity
#             discount = item.product.discount or 0
#             if discount==0:
#                 total_price_all = base_price * total_items
#             else:
#                 discounted_price = Decimal(1) - (
#                     Decimal(discount) / Decimal(100)
#                 )
#                 discounted_price = base_price * discounted_price
#                 total_price_all += discounted_price * total_items

#         return Response(
#             {
#                 "reservations": serializer.data,
#                 "total_price_all": total_price_all,
#             }
#         )

#     def post(self, request):
#         user = request.user
#         data = request.data.copy()
#         data["user"] = user.id  

#         serializer = self.serializer_class(data=data, context={"request": request})
#         if serializer.is_valid():
#             serializer.save()
#             return Response(
#                 {
#                     "message": "Reservation created successfully",
#                     "reservation": serializer.data,
#                 },
#                 status=status.HTTP_201_CREATED,
#             )
#         return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# class ModifyReserve(APIView):
#     serializer_class=[ModifyReserveSerializer]
#     permission_classes = [IsAuthenticated]
#     def delete(self,request,id):
#         try:
#             reservation = Reservation.objects.get(pk=id)
#             reservation.delete()
#             return Response({"message": "reservation deleted"})
#         except Reservation.DoesNotExist:
#             return Response({"message": "reservation not found"}, status=404)

# from users.permissions import IsAdminGroupUser
# from collections import defaultdict

# class AdminReservationView(APIView):
#     permission_classes = [IsAuthenticated, IsAdminGroupUser]
#     serializer_class = ReservationSerializer
#     def get(self, request):
#         reservs = Reservation.objects.select_related("user").all()
#         user_groups = defaultdict(list)
#         user_totals = defaultdict(Decimal)

#         for item in reservs:
#             user_groups[item.user].append(item)
#             price = item.product.price
#             discount = item.product.discount or 0
#             discounted_price = Decimal(price * (1 - discount / 100))
#             user_totals[item.user] += discounted_price * item.quantity

#         result = []
#         for user, items in user_groups.items():
#             serializer = ReservationSerializer(
#                 items, many=True, context={"request": request}
#             )
#             result.append(
#                 {
#                     "user_id": user.id,
#                     "username": user.phonenumber,
#                     "total_price": user_totals[user],
#                     "reservations": serializer.data,
#                 }
#             )

#         return Response(result)


# class SubmitReserveView(RateTimeBaseView, APIView):
#     permission_classes = [IsAuthenticated]
#     ratetime_class = [ThreePerMinuteLimit]
#     serializer_class = FinalizeReserveSerializer

#     def post(self, request):
#         user = request.user
#         serializer = self.serializer_class(
#             data=request.data, context={"request": request}
#         )

#         if not serializer.is_valid():
#             return Response(serializer.errors, status=400)

#         data = serializer.validated_data
#         reciver, reciver_phone = self._get_receiver_info(user, data)

#         location, delivery = self._get_location_and_delivery(data)
#         if not location or not delivery:
#             return Response({"error": "Invalid location or delivery slot."}, status=400)

#         if self._is_delivery_slot_full(delivery):
#             return Response({"error": "This delivery slot is full."}, status=400)

#         discount = self._get_discount(data.get("discount_text", ""))

#         cart_items = Reservation.objects.filter(user=user,date=data['date'],period=data['period'])
#         stock_issue = self._check_stock(cart_items)
#         if stock_issue:
#             return Response({"error": stock_issue}, status=400)

#         try:
#             order = self._create_order(
#                 user,
#                 data,
#                 location,
#                 delivery,
#                 reciver,
#                 reciver_phone,
#                 discount,
#                 cart_items,
#             )
#         except Exception as e:
#             return Response({"error": str(e)}, status=500)

#         callback_url = self._build_callback_url(request, order.id)
#         zarinpal = ZarinpalPayment(callback_url=callback_url)
#         payment_response = zarinpal.request(
#             user=user,
#             amount=int(order.total_price),
#             description=f"Order #{order.id} payment",
#             merchant_id=settings.MERCHANT_ID,
#         )

#         if payment_response.status_code != 200:
#             order.delete()
#             return payment_response

#         return Response(
#             {"payment_url": payment_response.data["payment_url"]}, status=200
#         )

#     def _get_receiver_info(self, user, data):
#         reciver = (
#             data.get("reciver")
#             if data.get("reciver") and data["reciver"] != "string"
#             else user.username
#         )
#         reciver_phone = (
#             data.get("reciver_phone")
#             if data.get("reciver_phone") and data["reciver_phone"] != "string"
#             else user.phonenumber
#         )
#         return reciver, reciver_phone

#     def _get_location_and_delivery(self, data):
#         try:
#             location = Location.objects.get(id=data["location_id"])
#             delivery = ReserveDeliverySlots.objects.get(id=data["deliver_time"])
#             return location, delivery
#         except (Location.DoesNotExist, ReserveDeliverySlots.DoesNotExist):
#             return None, None

#     def _is_delivery_slot_full(self, delivery):
#         return delivery.current_fill >= delivery.max_orders

#     def _get_discount(self, discount_text):
#         discount_text = discount_text.strip()
#         return (
#             DiscountCart.objects.filter(text=discount_text).first()
#             if discount_text
#             else None
#         )

#     def _check_stock(self, cart_items):
#         for item in cart_items:
#             if item.product.stock < item.quantity:
#                 return f"Not enough stock for {item.product.name}."
#         return None

#     def _create_order(
#         self,
#         user,
#         data,
#         location,
#         delivery,
#         reciver,
#         reciver_phone,
#         discount,
#         cart_items,
#     ):
#         with transaction.atomic():
#             order = Order.objects.create(
#                 location=location,
#                 user=user,
#                 delivery=delivery,
#                 description=data["description"],
#                 total_price=data["total_price"],
#                 profit=data["profit"],
#                 status=1,
#                 discount=discount,
#                 pay_status="pending",
#                 reciver=reciver,
#                 reciver_phone=reciver_phone,
#             )

#             for item in cart_items:
#                 OrderItem.objects.create(
#                     product=item.product,
#                     order=order,
#                     quantity=item.quantity,
#                     product_discount=item.product.discount,
#                 )
#                 item.product.stock -= item.quantity
#                 item.product.save()
#                 item.delete()

#             delivery.current_fill += 1
#             delivery.save()
#             return order

#     def _build_callback_url(self, request, order_id):
#         scheme = "https" if request.is_secure() else "http"
#         return (
#             f"{scheme}://{request.get_host()}/api/payment/verify/?order_id={order_id}"
#         )


# class ZarinpalVerifyView(RateTimeBaseView, APIView):
#     ratetime_class = [ThreePerMinuteLimit]

#     def get(self, request):
#         user = request.user
#         authority = request.GET.get("Authority")
#         status_query = request.GET.get("Status")
#         order_id = request.GET.get("order_id")

#         try:
#             transaction = ZarinpalTransaction.objects.get(authority=authority)
#             order = Order.objects.get(id=order_id)
#         except (ZarinpalTransaction.DoesNotExist, Order.DoesNotExist):
#             return Response({"message": "NOK"})
#         zarinpal = ZarinpalPayment(callback_url="")

#         result = zarinpal.verify(
#             status_query=status_query,
#             authority=authority,
#             merchant_id=settings.MERCHANT_ID,
#             amount=transaction.amount,
#         )
#         if result.status_code == 200:
#             order.pay_status = "paid"
#             order.save()
#             return Response({"message": "OK"})
#         else:
#             order.pay_status = "failed"
#             order.status = 0
#             order.save()
#             return Response({"message": "NOK"})


# # class OrderReservesView(APIView):
# #     permission_classes = [IsAuthenticated]
# #     serializer_class = OrderReservationSerializer

# #     def post(self, request):
# #         user = request.user
# #         serializer = self.serializer_class(data=request.data)

# #         if serializer.is_valid():
# #             if serializer.validated_data["is_paid"] is False:
# #                 return Response({"message": "You should pay"}, status=400)

# #             reservations = Reservation.objects.filter(user=user, active=True)

# #             if not reservations.exists():
# #                 return Response(
# #                     {"message": "No active reservations found."}, status=404
# #                 )

# #             total_price = 0
# #             for res in reservations:
# #                 base_price = res.product.price
# #                 discount = res.product.discount or 0
# #                 discounted_price = Decimal(base_price * (1 - discount / 100))
# #                 total_price += discounted_price * res.total_items

# #             location = reservations.first().location or "Unknown"
# #             delivery_time = reservations.first().next_delivery_date()

# #             order = Order.objects.create(
# #                 user=user,
# #                 location=location,
# #                 delivery_time=delivery_time,
# #                 total_price=round(total_price, 2),
# #             )

# #             for res in reservations:
# #                 OrderItem.objects.create(
# #                     order=order,
# #                     product=res.product,
# #                     quantity=res.quantity,
# #                     box_type=res.box_type,
# #                     product_discount=res.product.discount or 0,
# #                 )

# #             reservations.update(active=False)

# #             return Response(
# #                 {
# #                     "message": "Order created from reservations successfully",
# #                     "order_id": order.id,
# #                     "total_price": order.total_price,
# #                 },
# #                 status=201,
# #             )

# #         return Response(serializer.errors, status=400)
