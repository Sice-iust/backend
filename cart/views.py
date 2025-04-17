from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from product.models import *
from .models import *
from .serializers import *
from order.models import *
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from drf_spectacular.utils import extend_schema, OpenApiParameter
from django.utils import timezone
from rest_framework import status

User = get_user_model()


class CartView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.user
        cart_items = CartItem.objects.filter(user=user)
        serializer = CartSerializer(cart_items, many=True, context={"request": request})
        total_price = sum(item.product.price * item.quantity for item in cart_items)
        total_discount = sum(
            (item.product.price * item.product.discount / 100) * item.quantity
            for item in cart_items
        )
        total_actual_price = total_price - total_discount
        if total_actual_price<0:
            total_actual_price=0
        shipping_fee=0
        jalali_day = jdatetime.datetime.now().strftime("%A")

        if jalali_day in ["پنجشنبه", "جمعه"] and total_actual_price < 500000:
            shipping_fee = 50000  
        elif total_price == 0:
            shipping_fee = 0
        else:
            shipping_fee = 30000

        counts= CartItem.objects.filter(user=user).count()
        return Response(
            {
                "cart_items": serializer.data,
                "total_price": total_price,
                "total_discount": total_discount,
                "total_actual_price": total_actual_price,
                "total_with_shipping": total_actual_price+shipping_fee,
                "counts":counts,
            }
        )


class SingleCartView(APIView):
    serializer_class = CRUDCartSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        user = request.user
        product = get_object_or_404(Product, id=id)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            quantity = serializer.validated_data.get("quantity")

            if quantity is None or quantity <= 0:
                return Response({"error": "Enter quantity"}, status=400)
            if quantity > product.stock:
                return Response({"error": "Not enough stock available"}, status=400)
            if CartItem.objects.filter(user=user, product=product).exists():
                return Response(
                    {"error": "You already have this product in your cart"}, status=400
                )

            new_cart = CartItem.objects.create(
                user=user, product=product, quantity=quantity
            )
            new_cart.save()
            return Response({"success": "Cart saved"}, status=201)

        return Response(serializer.errors, status=400)

    def put(self, request, id):
        user = request.user
        product = get_object_or_404(Product, id=id)
        cart = CartItem.objects.filter(user=user, product=product).first()

        if not cart:
            return Response(
                {"error": "You don't have this product in your cart"}, status=404
            )

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            quantity = serializer.validated_data.get("quantity")

            if quantity is None or quantity <= 0:
                return Response({"error": "Enter quantity"}, status=400)
            if quantity > product.stock:
                return Response({"error": "Not enough stock available"}, status=400)

            cart.quantity = quantity
            cart.save()
            return Response({"success": "Cart updated"}, status=200)

        return Response(serializer.errors, status=400)

    def delete(self, request, id):
        user = request.user
        product = get_object_or_404(Product, id=id)

        cart_item = CartItem.objects.filter(user=user, product=product)
        if not cart_item.exists():
            return Response(
                {"error": "You don't have this product in your cart"}, status=404
            )

        cart_item.delete()
        return Response({"success": "Cart item deleted"}, status=200)


class HeaderView(APIView):
    def get(self, request):
        if not request.user.is_authenticated:
            return Response({"is_login": False})

        user = request.user
        cart_count = CartItem.objects.filter(user=user).count()

        return Response({
            "is_login": True,
            "username": user.username,
            "nums": cart_count
        })


class DiscountedCartView(APIView):
    serializer_class = CartDiscountSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        parameters=[
            OpenApiParameter(name='text', description='Discount code text', required=True, type=str),
        ]
    )
    def get(self, request):
        user = request.user
        text = request.query_params.get("text")

        if not text:
            return Response({"error": "Enter a Discount Code"}, status=400)

        discount_cart = DiscountCart.objects.filter(user=user, text=text).first()

        if not discount_cart:
            return Response({"error": "This discount cart does not exist."}, status=404)

        if discount_cart.expired_time and discount_cart.expired_time < timezone.now():
            return Response({"error": "Your discount cart is expired."}, status=400)

        if discount_cart.max_use <= 0:
            return Response(
                {"error": "This discount cart has been used too many times."},
                status=400,
            )

        if discount_cart.first_time:
            user_order_count = Order.objects.filter(user=user).count()
            if user_order_count > 0:
                return Response(
                    {"error": "This discount is only for your first order."}, status=400
                )

        cart_items = CartItem.objects.filter(user=user)

        if discount_cart.product:
            product_ids = cart_items.values_list("product_id", flat=True)
            if discount_cart.product.id not in product_ids:
                return Response(
                    {"error": "This discount is not for your products."}, status=400
                )
            if discount_cart.product.discount>10:
                return Response(
                    {"error": "This Product Has Discount."}, status=400
                )

        discount_cart.max_use -= 1
        discount_cart.save()

        total_price = 0
        total_discount = 0

        for item in cart_items:
            item_price = item.product.price * item.quantity
            item_discount = (
                item.product.price * item.product.discount / 100
            ) * item.quantity
            total_price += item_price
            total_discount += item_discount

        total_actual_price = total_price - total_discount
        if total_actual_price<discount_cart.payment_without_discount:
            return Response({"error":"This Discount is not for your payment."})

        if total_actual_price > discount_cart.max_discount and discount_cart.max_discount>0:
            final_price = total_actual_price - discount_cart.max_discount
            if total_actual_price < 0:
                total_actual_price = 0
            shipping_fee = 0
            jalali_day = jdatetime.datetime.now().strftime("%A")

            if jalali_day in ["پنجشنبه", "جمعه"] and total_actual_price < 500000:
                shipping_fee = 50000
            elif total_price == 0:
                shipping_fee = 0
            else:
                shipping_fee = 30000

            serializer = self.serializer_class(
                {
                    "final_price": final_price,
                    "discount": discount_cart.max_discount + total_discount,
                    "final_with_shipping": final_price + shipping_fee,
                }
            )
            return Response(serializer.data)

        percentage_discount = (total_actual_price * discount_cart.percentage) / 100
        final_price = total_actual_price - percentage_discount
        total_actual_price = total_price - total_discount
        if total_actual_price<0:
            total_actual_price=0
        shipping_fee = 0
        jalali_day = jdatetime.datetime.now().strftime("%A")

        if jalali_day in ["پنجشنبه", "جمعه"] and total_actual_price < 500000:
            shipping_fee = 50000
        elif total_price == 0:
            shipping_fee = 0
        else:
            shipping_fee = 30000

        serializer = self.serializer_class(
            {
                "final_price": final_price,
                "discount": percentage_discount + total_discount,
                "final_with_shipping":final_price+shipping_fee
            }
        )
        return Response(serializer.data)
