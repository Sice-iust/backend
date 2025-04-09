from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import ListAPIView
from product.models import *
from .models import *
from .serializers import *

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

        return Response(
            {
                "cart_items": serializer.data,
                "total_price": total_price,
                "total_discount": total_discount,
                "total_actual_price": total_actual_price,
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