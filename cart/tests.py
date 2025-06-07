from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from product.models import Product
from .models import CartItem, DeliveryCart
from order.models import DeliverySlots
from decimal import Decimal
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from rest_framework import serializers

User = get_user_model()
class CartViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="fati@gmail.com",
            phonenumber="+989034488755"
        )
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        self.product = Product.objects.create(
            name="Test Bread",
            price=10000,
            discount=10,  
            category="نان بربری",
            box_type=4,
        )
        self.url = reverse("cart")

    def test_cart_with_no_items(self):
        """User has no cart items"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["cart_items"], [])
        self.assertEqual(response.data["total_discount"], 0)
        self.assertEqual(response.data["total_actual_price"], 0)
        self.assertEqual(response.data["shipping_fee"], -1)
        self.assertEqual(response.data["total_actual_price_with_shipp"], -1)
        self.assertEqual(response.data["counts"], 0)

    def test_cart_with_one_item_no_discount(self):
        """One cart item with no discount"""
        product = Product.objects.create(name="Bread", price=100, discount=0, box_type=1, category="نان بربری")
        CartItem.objects.create(user=self.user, product=product, quantity=2)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_discount"], 0)
        self.assertEqual(response.data["total_actual_price"], 200)
        self.assertEqual(response.data["counts"], 1)

    def test_cart_with_discounted_item(self):
        """Cart item with 10% discount"""
        product = Product.objects.create(name="Bread", price=100, discount=10, box_type=1, category="نان بربری")
        CartItem.objects.create(user=self.user, product=product, quantity=3)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_discount"], 30)  # 3 * (100*10%)
        self.assertEqual(response.data["total_actual_price"], 270)

    def test_cart_with_multiple_items(self):
        """Cart with multiple products with and without discount"""
        p1 = Product.objects.create(name="A", price=100, discount=10, box_type=1, category="نان بربری")
        p2 = Product.objects.create(name="B", price=200, discount=0, box_type=2, category="نان سنگک")
        CartItem.objects.create(user=self.user, product=p1, quantity=2)  # 200 - 20
        CartItem.objects.create(user=self.user, product=p2, quantity=1)  # 200
        response = self.client.get(self.url)
        self.assertEqual(response.data["total_discount"], 20)
        self.assertEqual(response.data["total_actual_price"], 380)
        self.assertEqual(response.data["counts"], 2)

    def test_cart_with_valid_delivery(self):
        """Cart with valid delivery slot"""
        product = Product.objects.create(name="Bread", price=100, discount=0, box_type=1, category="نان بربری")
        CartItem.objects.create(user=self.user, product=product, quantity=1)
        delivery_slot = DeliverySlots.objects.create(
            start_time="10:00", end_time="12:00", delivery_date=timezone.now().date(),
            max_orders=10, current_fill=5, shipping_fee=50
        )
        DeliveryCart.objects.create(user=self.user, delivery=delivery_slot)
        response = self.client.get(self.url)
        self.assertEqual(response.data["shipping_fee"], 50)
        self.assertEqual(response.data["total_actual_price_with_shipp"], 150)

    def test_cart_with_invalid_delivery_date(self):
        """DeliveryCart exists but delivery is in the past"""
        product = Product.objects.create(name="Bread", price=100, discount=0, box_type=1, category="نان بربری")
        CartItem.objects.create(user=self.user, product=product, quantity=1)
        delivery_slot = DeliverySlots.objects.create(
            start_time="10:00", end_time="12:00", delivery_date=timezone.now().date() - timezone.timedelta(days=1),
            max_orders=10, current_fill=5, shipping_fee=60
        )
        DeliveryCart.objects.create(user=self.user, delivery=delivery_slot)
        response = self.client.get(self.url)
        self.assertEqual(response.data["shipping_fee"], -1)

    def test_cart_with_fully_booked_delivery(self):
        """DeliveryCart exists but it's full"""
        product = Product.objects.create(name="Bread", price=100, discount=0, box_type=1, category="نان بربری")
        CartItem.objects.create(user=self.user, product=product, quantity=1)
        delivery_slot = DeliverySlots.objects.create(
            start_time="10:00", end_time="12:00", delivery_date=timezone.now().date(),
            max_orders=10, current_fill=10, shipping_fee=70
        )
        DeliveryCart.objects.create(user=self.user, delivery=delivery_slot)
        response = self.client.get(self.url)
        self.assertEqual(response.data["shipping_fee"], -1)

    def test_unauthenticated_user(self):
        """Unauthenticated users get 403"""
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)


class SingleCartViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser2",
            password="testpass",
            email="testuser2@gmail.com",
            phonenumber="+989012345678",
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        self.product = Product.objects.create(
            name="Test Bread",
            price=10000,
            discount=10,
            category="نان بربری",
            box_type=4,
        )
        self.url = lambda product_id: reverse(
            "cart-single", args=[product_id]
        ) 

    def test_add_product_successfully(self):

        response = self.client.post(self.url(self.product.id), {"quantity": 2})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["success"], "Cart saved")
        self.assertEqual(CartItem.objects.count(), 1)
        self.assertEqual(CartItem.objects.first().quantity, 2)

    def test_invalid_product_id(self):

        response = self.client.post(self.url(9999), {"quantity": 1})
        self.assertEqual(response.status_code, 404)

    def test_missing_quantity(self):

        response = self.client.post(self.url(self.product.id), {})
        self.assertEqual(response.status_code, 400)
        self.assertIn("quantity", response.data)

    def test_zero_or_negative_quantity(self):

        for invalid_quantity in [0, -1, -100]:
            response = self.client.post(
                self.url(self.product.id), {"quantity": invalid_quantity}
            )
            self.assertEqual(response.status_code, 200)
            self.assertIn("you should enter positive", str(response.data).lower())

    def test_duplicate_cart_item(self):

        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        response = self.client.post(self.url(self.product.id), {"quantity": 2})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(
            response.data["error"], "You already have this product in your cart"
        )

    def test_unauthenticated_user(self):

        self.client.credentials()
        response = self.client.post(self.url(self.product.id), {"quantity": 1})
        self.assertEqual(response.status_code, 401)

    def test_large_quantity(self):

        response = self.client.post(self.url(self.product.id), {"quantity": 999})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(CartItem.objects.first().quantity, 999)

    def test_non_integer_quantity(self):

        response = self.client.post(self.url(self.product.id), {"quantity": "two"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("quantity", response.data)

    def test_extra_fields_ignored(self):

        response = self.client.post(
            self.url(self.product.id), {"quantity": 3, "random_field": "ignore me"}
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(CartItem.objects.first().quantity, 3)

    def test_quantity_boundary_one(self):

        response = self.client.post(self.url(self.product.id), {"quantity": 1})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(CartItem.objects.first().quantity, 1)


class SingleModifyCartViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="testuser@gmail.com",
            phonenumber="+989011112233",
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        self.product = Product.objects.create(
            name="Test Product",
            price=20000,
            discount=5,
            category="نان سنگک",
            box_type=2,
        )
        self.modify_url = lambda id: reverse(
            "cart-single-modify", args=[id]
        )  

    def test_put_missing_update_mode(self):
        response = self.client.put(self.modify_url(self.product.id))
        self.assertEqual(response.status_code, 400)
        self.assertIn("Enter Update Mode", response.data["error"])

    def test_put_product_not_in_cart(self):
        response = self.client.put(self.modify_url(self.product.id) + "?update=add")
        self.assertEqual(response.status_code, 404)
        self.assertIn("don't have this product", response.data["error"])

    def test_put_invalid_product_id(self):
        response = self.client.put(
            reverse("cart-single-modify", args=[9999]) + "?update=add"
        )
        self.assertEqual(response.status_code, 404)

    def test_put_add_quantity(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        response = self.client.put(self.modify_url(self.product.id) + "?update=add")
        self.assertEqual(response.status_code, 200)
        self.assertIn("Cart updated", response.data["success"])
        self.assertEqual(CartItem.objects.first().quantity, 2)

    def test_put_delete_quantity_above_one(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=3)
        response = self.client.put(self.modify_url(self.product.id) + "?update=delete")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.first().quantity, 2)

    def test_put_delete_quantity_equals_one(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        response = self.client.put(self.modify_url(self.product.id) + "?update=delete")
        self.assertEqual(response.status_code, 200)
        self.assertIn("you should delete it", response.data["message"])

    def test_put_invalid_update_mode(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        response = self.client.put(
            self.modify_url(self.product.id) + "?update=invalid_mode"
        )
        self.assertEqual(response.status_code, 400)

    def test_delete_cart_item_successfully(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=2)
        response = self.client.delete(self.modify_url(self.product.id))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["success"], "Cart item deleted")
        self.assertEqual(CartItem.objects.count(), 0)

    def test_delete_cart_item_not_in_cart(self):
        response = self.client.delete(self.modify_url(self.product.id))
        self.assertEqual(response.status_code, 404)
        self.assertIn("don't have this product", response.data["error"])

    def test_delete_invalid_product_id(self):
        response = self.client.delete(reverse("cart-single-modify", args=[9999]))
        self.assertEqual(response.status_code, 404)


class HeaderViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser100",
            password="testpass",
            email="test@example.com",
            phonenumber="+989123456789",
        )
        self.product = Product.objects.create(
            name="Test Bread", price=10000, discount=0, category="نان بربری", box_type=1
        )
        self.url = reverse("header") 

    def test_unauthenticated_user(self):
        """Returns is_login False if not authenticated"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["is_login"], False)

    def test_authenticated_user_no_cart_items(self):
        """Authenticated user with no cart items"""
        token = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(token.access_token)}")

        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["is_login"], True)
        self.assertEqual(response.data["username"], self.user.username)
        self.assertEqual(response.data["nums"], 0)


class QuentityViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass123",
            email="test@example.com",
            phonenumber="+989123456789",
        )
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.url = reverse("quentity") 

        self.product1 = Product.objects.create(
            name="Bread A", price=10000, discount=0, category="نان بربری", box_type=1
        )
        self.product2 = Product.objects.create(
            name="Bread B", price=20000, discount=5, category="نان سنگک", box_type=2
        )

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

    def test_authenticated_user_with_multiple_cart_items(self):
        """Authenticated user sees list of product_id and quantity for each item"""
        CartItem.objects.create(user=self.user, product=self.product1, quantity=3)
        CartItem.objects.create(user=self.user, product=self.product2, quantity=2)

        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        self.assertIn({"product_id": self.product1.id, "quantity": 3}, response.data)
        self.assertIn({"product_id": self.product2.id, "quantity": 2}, response.data)

    def test_authenticated_user_with_no_cart_items(self):
        """Authenticated user with empty cart receives an empty list"""
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, [])

    def test_unauthenticated_user_access(self):
        """Unauthenticated user gets 401 Unauthorized"""
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 401)

    def test_cart_items_belong_to_other_users_not_included(self):
        """Cart items from other users are not shown"""
        other_user = User.objects.create_user(
            username="otheruser",
            password="otherpass",
            email="other@example.com",
            phonenumber="+989111111111",
        )
        CartItem.objects.create(user=other_user, product=self.product1, quantity=5)
        CartItem.objects.create(user=self.user, product=self.product2, quantity=1)

        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["product_id"], self.product2.id)
        self.assertEqual(response.data[0]["quantity"], 1)

    def test_cart_item_quantity_is_positive_integer(self):
        """Ensure the quantities returned are positive integers"""
        CartItem.objects.create(user=self.user, product=self.product1, quantity=3)
        self.authenticate()
        response = self.client.get(self.url)
        quantity = response.data[0]["quantity"]
        self.assertIsInstance(quantity, int)
        self.assertGreater(quantity, 0)

    def test_large_quantity_values(self):
        """Test if large quantity values are returned correctly"""
        large_quantity = 1000000
        CartItem.objects.create(
            user=self.user, product=self.product1, quantity=large_quantity
        )
        self.authenticate()
        response = self.client.get(self.url)
        self.assertEqual(response.data[0]["quantity"], large_quantity)

 