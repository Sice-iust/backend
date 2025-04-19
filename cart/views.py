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
        serializer = SummerizedCartSerializer(
            cart_items, many=True, context={"request": request}
        )
        total_price = 0
        total_discount = 0

        for item in cart_items:
            price = item.product.price or 0
            discount = item.product.discount or 0
            quantity = item.quantity

            total_price += price * quantity * item.box_type
            total_discount += (price * discount / 100) * quantity * item.box_type

        total_actual_price = total_price - total_discount
        if total_actual_price<0:
            total_actual_price=0


        counts= CartItem.objects.filter(user=user).count()
        return Response(
            {
                "cart_items": serializer.data,
                "total_discount": total_discount,
                "total_actual_price": total_actual_price,
                "counts":counts,
            }
        )


class SingleCartView(APIView):
    serializer_class = CRUDCartSerializer
    permission_classes = [IsAuthenticated]

    def validate_quantity(self, quantity, box_type, product):
        if quantity is None or quantity <= 0:
            return "Enter quantity"

        stock_dict = {
            1: product.stock_1,
            2: product.stock_2,
            4: product.stock_4,
            6: product.stock_6,
            8: product.stock_8,
        }

        if box_type not in stock_dict:
            return "Invalid box type"

        if quantity > stock_dict[box_type]:
            return "Not enough stock available"

        return None

    def post(self, request, id, box_type):
        user = request.user
        product = get_object_or_404(Product, id=id)

        if box_type not in [1,2, 4, 6, 8]:
            return Response({"error": "Invalid box type"}, status=400)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            quantity = serializer.validated_data.get("quantity")

            error_message = self.validate_quantity(quantity, box_type, product)
            if error_message:
                return Response({"error": error_message}, status=400)

            if CartItem.objects.filter(
                user=user, product=product, box_type=box_type
            ).exists():
                return Response(
                    {"error": "You already have this product in your cart"}, status=400
                )

            new_cart = CartItem.objects.create(
                user=user, product=product, quantity=quantity, box_type=box_type
            )
            return Response({"success": "Cart saved"}, status=201)

        return Response(serializer.errors, status=400)

    def put(self, request, id, box_type):
        user = request.user
        product = get_object_or_404(Product, id=id)
        cart = CartItem.objects.filter(
            user=user, product=product, box_type=box_type
        ).first()

        if not cart:
            return Response(
                {"error": "You don't have this product in your cart"}, status=404
            )

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            quantity = serializer.validated_data.get("quantity")

            error_message = self.validate_quantity(quantity, box_type, product)
            if error_message:
                return Response({"error": error_message}, status=400)

            cart.quantity = quantity
            cart.save()
            return Response({"success": "Cart updated"}, status=200)

        return Response(serializer.errors, status=400)

    def delete(self, request, id, box_type):
        user = request.user
        product = get_object_or_404(Product, id=id)

        cart_item = CartItem.objects.filter(
            user=user, product=product, box_type=box_type
        )
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
            item_price = item.product.price * item.quantity * item.box_type
            item_discount = (
                item.product.price * item.product.discount / 100
            ) * item.quantity *item.box_type
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


class QuentityView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = QuentitySerializer

    def get(self, request, id):
        user = request.user
        cart_items = CartItem.objects.filter(user=user, product_id=id)

        all_box_types = dict(CartItem.BOX_CHOICES)
        box_quantity = {f"Box_of_{key}": 0 for key in all_box_types}

        for item in cart_items:
            label = f"Box_of_{item.box_type}"
            box_quantity[label] += item.quantity

        data = {"product_id": id, "box_quantities": box_quantity}

        serializer = self.serializer_class(instance=data)
        return Response(serializer.data)
