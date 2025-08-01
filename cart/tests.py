from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from django.contrib.auth import get_user_model
from product.models import Product,Category
from .models import CartItem, DeliveryCart
from order.models import DeliverySlots
from decimal import Decimal
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from rest_framework import serializers
from django.test import TestCase
from cart.serializers import SummerizedCartSerializer
from .views import *
from unittest.mock import patch, MagicMock
from rest_framework.test import APIRequestFactory,force_authenticate
from rest_framework import status

User = get_user_model()

class QuentityViewUnitTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = QuentityView.as_view()
        self.user = MagicMock()
        self.user.id = 1

    @patch("cart.views.CartItem.objects.filter")
    def test_get_cart_items(self, mock_filter):
        mock_cart_items = [MagicMock(), MagicMock()]
        mock_filter.return_value.all.return_value = mock_cart_items

        request = self.factory.get("/fake-url/")
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), len(mock_cart_items))


class DeliveryViewUnitTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = DeliveryView.as_view()
        self.user = MagicMock()
        self.user.id = 1

    @patch("cart.views.DeliveryCart.objects.filter")
    def test_get_no_delivery_cart(self, mock_filter):
        mock_filter.return_value.last.return_value = None

        request = self.factory.get("/fake-url/")
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, 404)
        self.assertIn("No delivery found", response.data["detail"])



class CartDeliveryViewUnitTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.view = CartDeliveryView.as_view()
        self.user = MagicMock()
        self.user.id = 1

    @patch("cart.views.DeliverySlots.objects.get")
    def test_post_delivery_slot_not_found(self, mock_get):
        mock_get.side_effect = DeliverySlots.DoesNotExist

        request = self.factory.post("/fake-url/")
        force_authenticate(request, user=self.user)
        response = self.view(request, delivery_id=999)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Delivery slot not found", response.data["error"])

    @patch("cart.views.DeliverySlots.objects.get")
    def test_post_delivery_slot_in_past(self, mock_get):
        delivery_mock = MagicMock()
        delivery_mock.delivery_date = timezone.now().date() - timezone.timedelta(days=1)
        mock_get.return_value = delivery_mock

        request = self.factory.post("/fake-url/")
        force_authenticate(request, user=self.user)
        response = self.view(request, delivery_id=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Cannot assign a past or current delivery slot", response.data["error"]
        )

    @patch("cart.views.CartItem.objects.filter")
    @patch("cart.views.DeliverySlots.objects.get")
    @patch("cart.views.DeliveryCart.objects.update_or_create")
    def test_post_no_cart_items(
        self, mock_update_or_create, mock_get, mock_cart_filter
    ):
        delivery_mock = MagicMock()
        delivery_mock.delivery_date = timezone.now().date() + timezone.timedelta(days=1)
        mock_get.return_value = delivery_mock

        mock_cart_filter.return_value.exists.return_value = False

        request = self.factory.post("/fake-url/")
        force_authenticate(request, user=self.user)
        response = self.view(request, delivery_id=1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("User has no cart items", response.data["error"])
        mock_update_or_create.assert_not_called()

    @patch("cart.views.CartItem.objects.filter")
    @patch("cart.views.DeliverySlots.objects.get")
    @patch("cart.views.DeliveryCart.objects.update_or_create")
    def test_post_assign_delivery_success(
        self, mock_update_or_create, mock_get, mock_cart_filter
    ):
        delivery_mock = MagicMock()
        delivery_mock.delivery_date = timezone.now().date() + timezone.timedelta(days=1)
        mock_get.return_value = delivery_mock

        mock_cart_filter.return_value.exists.return_value = True

        request = self.factory.post("/fake-url/")
        force_authenticate(request, user=self.user)
        response = self.view(request, delivery_id=1)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn(
            "Delivery assigned to cart successfully", response.data["message"]
        )
        mock_update_or_create.assert_called_once_with(
            user=self.user, defaults={"delivery": delivery_mock}
        )


class DiscountedCartViewUnitTest(TestCase):
    def setUp(self):
        self.view = DiscountedCartView.as_view()
        self.factory = APIRequestFactory()
        self.user = MagicMock()
        self.user.id = 1

    def test_get_discount_no_code(self):
        view = DiscountedCartView()
        error, status_code = view.get_discount(self.user, None)
        self.assertEqual(status_code, 400)
        self.assertIn("Enter a Discount Code", error["error"])

    @patch("cart.views.DiscountCart.objects.filter")
    def test_get_discount_not_found(self, mock_filter):
        mock_filter.return_value.first.return_value = None
        view = DiscountedCartView()
        error, status_code = view.get_discount(self.user, "invalidcode")
        self.assertEqual(status_code, 404)
        self.assertIn("does not exist", error["error"])

    def test_get_discount_expired(self):
        discount = MagicMock()
        discount.expired_time = timezone.now() - timezone.timedelta(days=1)
        discount.max_use = 1
        discount.first_time = False
        discount.payment_without_discount = 0
        discount.product = None

        with patch("cart.views.DiscountCart.objects.filter") as mock_filter:
            mock_filter.return_value.first.return_value = discount
            view = DiscountedCartView()
            error, status_code = view.get_discount(self.user, "code")
            self.assertEqual(status_code, 400)
            self.assertIn("expired", error["error"])

    def test_get_discount_max_use_zero(self):
        discount = MagicMock()
        discount.expired_time = None
        discount.max_use = 0
        discount.first_time = False
        discount.payment_without_discount = 0
        discount.product = None

        with patch("cart.views.DiscountCart.objects.filter") as mock_filter:
            mock_filter.return_value.first.return_value = discount
            view = DiscountedCartView()
            error, status_code = view.get_discount(self.user, "code")
            self.assertEqual(status_code, 400)
            self.assertIn("been used too many times", error["error"])

    def test_get_discount_first_time_user_has_order(self):
        discount = MagicMock()
        discount.expired_time = None
        discount.max_use = 1
        discount.first_time = True
        discount.payment_without_discount = 0
        discount.product = None

        with patch(
            "cart.views.DiscountCart.objects.filter"
        ) as mock_filter_discount, patch(
            "cart.views.Order.objects.filter"
        ) as mock_order_filter:
            mock_filter_discount.return_value.first.return_value = discount
            mock_order_filter.return_value.exists.return_value = True
            view = DiscountedCartView()
            error, status_code = view.get_discount(self.user, "code")
            self.assertEqual(status_code, 400)
            self.assertIn("only for your first order", error["error"])

    def test_calculate_prices_empty_cart(self):
        discount = MagicMock()
        discount.product = None

        with patch("cart.views.CartItem.objects.filter") as mock_cart:
            mock_cart.return_value.exists.return_value = False
            view = DiscountedCartView()
            error, status_code, prices = view.calculate_prices(self.user, discount)
            self.assertEqual(status_code, 400)
            self.assertIn("cart is empty", error["error"])

    def test_calculate_prices_discount_product_not_in_cart(self):
        discount = MagicMock()
        discount.product = MagicMock()
        discount.product.id = 1

        with patch("cart.views.CartItem.objects.filter") as mock_cart:
            mock_cart.return_value.exists.return_value = True
            mock_cart.return_value.values_list.return_value = [
                2,
                3,
            ]

            view = DiscountedCartView()
            error, status_code, prices = view.calculate_prices(self.user, discount)
            self.assertEqual(status_code, 400)
            self.assertIn("not for your products", error["error"])

    def test_calculate_prices_product_has_high_discount(self):
        discount = MagicMock()
        product = MagicMock()
        product.discount = 20  
        discount.product = product

        cart_item = MagicMock()
        cart_item.product = product
        cart_item.quantity = 1

        with patch("cart.views.CartItem.objects.filter") as mock_cart:
            mock_cart.return_value.exists.return_value = True
            mock_cart.return_value.values_list.return_value = [product.id]
            mock_cart.return_value.__iter__.return_value = [cart_item]

            view = DiscountedCartView()
            error, status_code, prices = view.calculate_prices(self.user, discount)
            self.assertEqual(status_code, 400)
            self.assertIn("already has a discount", error["error"])

    def test_calculate_prices_payment_without_discount_fail(self):
        discount = MagicMock()
        discount.payment_without_discount = 5000
        discount.product = None

        product = MagicMock()
        product.price = 1000
        product.discount = 0

        cart_item = MagicMock()
        cart_item.product = product
        cart_item.quantity = 3  

        with patch("cart.views.CartItem.objects.filter") as mock_cart:
            mock_cart.return_value.exists.return_value = True
            mock_cart.return_value.__iter__.return_value = [cart_item]

            view = DiscountedCartView()
            error, status_code, prices = view.calculate_prices(self.user, discount)
            self.assertEqual(status_code, 400)
            self.assertIn("not valid for your payment", error["error"])

    @patch("cart.views.DeliveryCart.objects.filter")
    @patch("cart.views.CartItem.objects.filter")
    @patch("cart.views.DiscountCart.objects.filter")
    def test_get_successful_response(
        self, mock_discount_filter, mock_cart_filter, mock_delivery_filter
    ):
        discount = MagicMock()
        discount.expired_time = None
        discount.max_use = 5
        discount.first_time = False
        discount.product = None
        discount.payment_without_discount = 0
        discount.max_discount = 1000
        discount.percentage = 10

        mock_discount_filter.return_value.first.return_value = discount


        product = MagicMock()
        product.price = 1000
        product.discount = 0

        cart_item = MagicMock()
        cart_item.product = product
        cart_item.quantity = 2

        mock_cart_filter.return_value.exists.return_value = True
        mock_cart_filter.return_value.__iter__.return_value = [cart_item]

       
        delivery = MagicMock()
        delivery.delivery_date = timezone.now().date()
        delivery.current_fill = 0
        delivery.max_orders = 10
        delivery.shipping_fee = 100

        mock_delivery_cart = MagicMock()
        mock_delivery_cart.delivery = delivery
        mock_delivery_filter.return_value.last.return_value = mock_delivery_cart

        request = self.factory.get("/fake-url/?text=discountcode")
        force_authenticate(request, user=self.user)
        response = self.view(request)

        self.assertEqual(response.status_code, 200)
        self.assertIn("final_price", response.data)
        self.assertIn("discount", response.data)
        discount.save.assert_called_once()


class SingleCartViewUnitTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = MagicMock(spec=User)
        self.user.id = 1
        self.view = SingleCartView.as_view()

    @patch("cart.views.get_object_or_404")
    @patch("cart.views.CartItem.objects.filter")
    @patch("cart.views.CartItem.objects.create")
    def test_post_success(self, mock_create, mock_filter, mock_get):
     
        product = MagicMock()
        mock_get.return_value = product

      
        mock_filter.return_value.exists.return_value = False

        mock_create.return_value = MagicMock()

        data = {"quantity": 3}
        request = self.factory.post("/fake-url/", data, format="json")
        force_authenticate(request, user=self.user)

        response = self.view(request, id=1)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["success"], "Cart saved")
        mock_create.assert_called_once_with(user=self.user, product=product, quantity=3)

    @patch("cart.views.get_object_or_404")
    def test_post_quantity_zero_or_negative(self, mock_get):
        product = MagicMock()
        mock_get.return_value = product

        data = {"quantity": 0}
        request = self.factory.post("/fake-url/", data, format="json")
        force_authenticate(request, user=self.user)

        response = self.view(request, id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, "you should enter positive.")

        data = {"quantity": -5}
        request = self.factory.post("/fake-url/", data, format="json")
        force_authenticate(request, user=self.user)

        response = self.view(request, id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, "you should enter positive.")

    @patch("cart.views.get_object_or_404")
    @patch("cart.views.CartItem.objects.filter")
    def test_post_product_already_in_cart(self, mock_filter, mock_get):
        product = MagicMock()
        mock_get.return_value = product

        mock_filter.return_value.exists.return_value = True

        data = {"quantity": 2}
        request = self.factory.post("/fake-url/", data, format="json")
        force_authenticate(request, user=self.user)

        response = self.view(request, id=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(
            response.data["error"], "You already have this product in your cart"
        )


class SingleModifyCartViewUnitTest(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = MagicMock(spec=User)
        self.user.id = 1

    @patch("cart.views.get_object_or_404")
    @patch("cart.views.CartItem.objects.filter")
    def test_put_missing_update_mode(self, mock_filter, mock_get):
        request = self.factory.put("/fake-url/")
        request.user = self.user
        force_authenticate(request, user=self.user)

        response = SingleModifyCartView.as_view()(request, id=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Enter Update Mode", response.data["error"])

    @patch("cart.views.get_object_or_404")
    @patch("cart.views.CartItem.objects.filter")
    def test_put_product_not_in_cart(self, mock_filter, mock_get):
        mock_get.return_value = MagicMock()  # product
        mock_filter.return_value.first.return_value = None

        request = self.factory.put("/fake-url/?update=add")
        force_authenticate(request, user=self.user)
        request.user = self.user

        response = SingleModifyCartView.as_view()(request, id=1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("don't have this product", response.data["error"])

    @patch("cart.views.get_object_or_404")
    @patch("cart.views.CartItem.objects.filter")
    def test_put_add_quantity_success(self, mock_filter, mock_get):
        product = MagicMock()
        mock_get.return_value = product

        cart_item = MagicMock()
        cart_item.quantity = 1
        cart_item.save = MagicMock()
        mock_filter.return_value.first.return_value = cart_item

        request = self.factory.put("/fake-url/?update=add")
        force_authenticate(request, user=self.user)
        request.user = self.user

        response = SingleModifyCartView.as_view()(request, id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_item.save.assert_called_once()
        self.assertEqual(cart_item.quantity, 2)

    @patch("cart.views.get_object_or_404")
    @patch("cart.views.CartItem.objects.filter")
    def test_put_delete_quantity_above_one(self, mock_filter, mock_get):
        mock_get.return_value = MagicMock()

        cart_item = MagicMock()
        cart_item.quantity = 3
        cart_item.save = MagicMock()
        mock_filter.return_value.first.return_value = cart_item

        request = self.factory.put("/fake-url/?update=delete")
        force_authenticate(request, user=self.user)
        request.user = self.user

        response = SingleModifyCartView.as_view()(request, id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_item.save.assert_called_once()
        self.assertEqual(cart_item.quantity, 2)

    @patch("cart.views.get_object_or_404")
    @patch("cart.views.CartItem.objects.filter")
    def test_put_delete_quantity_equals_one(self, mock_filter, mock_get):
        mock_get.return_value = MagicMock()

        cart_item = MagicMock()
        cart_item.quantity = 1
        mock_filter.return_value.first.return_value = cart_item

        request = self.factory.put("/fake-url/?update=delete")
        force_authenticate(request, user=self.user)
        request.user = self.user

        response = SingleModifyCartView.as_view()(request, id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("you should delete it", response.data["message"])

    @patch("cart.views.get_object_or_404")
    @patch("cart.views.CartItem.objects.filter")
    def test_put_invalid_update_mode(self, mock_filter, mock_get):
        mock_get.return_value = MagicMock()
        cart_item = MagicMock()
        mock_filter.return_value.first.return_value = cart_item

        request = self.factory.put("/fake-url/?update=invalid_mode")
        force_authenticate(request, user=self.user)
        request.user = self.user

        response = SingleModifyCartView.as_view()(request, id=1)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Invalid update mode", response.data["error"])

    @patch("cart.views.get_object_or_404")
    @patch("cart.views.CartItem.objects.filter")
    def test_delete_cart_item_successfully(self, mock_filter, mock_get):
        mock_get.return_value = MagicMock()

        cart_qs = MagicMock()
        cart_qs.exists.return_value = True
        cart_qs.delete = MagicMock()
        mock_filter.return_value = cart_qs

        request = self.factory.delete("/fake-url/")
        force_authenticate(request, user=self.user)
        request.user = self.user

        response = SingleModifyCartView.as_view()(request, id=1)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cart_qs.delete.assert_called_once()
        self.assertEqual(response.data["success"], "Cart item deleted")

    @patch("cart.views.get_object_or_404")
    @patch("cart.views.CartItem.objects.filter")
    def test_delete_cart_item_not_in_cart(self, mock_filter, mock_get):
        mock_get.return_value = MagicMock()

        cart_qs = MagicMock()
        cart_qs.exists.return_value = False
        mock_filter.return_value = cart_qs

        request = self.factory.delete("/fake-url/")
        force_authenticate(request, user=self.user)
        request.user = self.user

        response = SingleModifyCartView.as_view()(request, id=1)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("don't have this product", response.data["error"])

class CartViewUnitTest(TestCase):
    def setUp(self):
        self.cart_view = CartView()
        self.user = User.objects.create(phonenumber="+989120000000")
        self.category = Category.objects.create(category="نان", box_color="red")
        self.product = Product.objects.create(
            name="Bread",
            price=1000,
            discount=10,
            category=self.category,
            box_type=2,
        )

    def test_calculate_cart_totals_empty_cart(self):
        result = self.cart_view.calculate_cart_totals(self.user)
        self.assertEqual(result["total_discount"], 0)
        self.assertEqual(result["total_actual_price"], 0)
        self.assertEqual(result["shipping_fee"], -1)
        self.assertEqual(result["counts"], 0)

    def test_calculate_cart_totals_with_items_and_delivery(self):
        CartItem.objects.create(user=self.user, product=self.product, quantity=3)

        delivery_slot = DeliverySlots.objects.create(
            start_time="10:00",
            end_time="12:00",
            delivery_date=timezone.now().date(),
            max_orders=10,
            current_fill=5,
            shipping_fee=50,
        )
        DeliveryCart.objects.create(user=self.user, delivery=delivery_slot)

        result = self.cart_view.calculate_cart_totals(self.user)

        expected_price = 1000 * 3
        expected_discount = expected_price * 0.10
        expected_actual = expected_price - expected_discount

        self.assertEqual(result["total_discount"], expected_discount)
        self.assertEqual(result["total_actual_price"], expected_actual)
        self.assertEqual(result["shipping_fee"], 50)
        self.assertEqual(result["counts"], 1)


class SummerizedCartSerializerTests(TestCase):
    def test_get_price(self):
        user = User.objects.create(phonenumber="+989120000000")
        product = Product.objects.create(name="Test Bread", price=1000, discount=10)
        cart_item = CartItem.objects.create(user=user, product=product, quantity=2)

        serializer = SummerizedCartSerializer()
        result = serializer.get_price(cart_item)
        self.assertEqual(result, 2000)

    def test_get_discountedprice(self):
        user = User.objects.create(phonenumber="+989120000000")
        product = Product.objects.create(name="Test Bread", price=1000, discount=10)
        cart_item = CartItem.objects.create(user=user, product=product, quantity=2)

        serializer = SummerizedCartSerializer()
        result = serializer.get_discountedprice(cart_item)
        expected_discounted_price = 2000 - 200  # 10% of 2000
        self.assertEqual(result, expected_discounted_price)


class CartItemModelTests(TestCase):
    def test_total_items_property(self):
        user = User.objects.create(phonenumber="+989120000000")
        product = Product.objects.create(
            name="Test Bread", price=1000, discount=0, box_type=5
        )
        cart_item = CartItem.objects.create(user=user, product=product, quantity=3)

        self.assertEqual(cart_item.total_items, 15)  # 5 * 3

    def test_cartitem_str(self):
        user = User.objects.create(phonenumber="+989120000000")
        product = Product.objects.create(
            name="Test Bread", price=1000, discount=0, box_type=5
        )
        cart_item = CartItem.objects.create(user=user, product=product, quantity=2)

        expected = "Test Bread - +989120000000 | 2 x box of 5 = 10 items"
        self.assertEqual(str(cart_item), expected)


class CartViewTests(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            password="testpass",
            email="fati@gmail.com",
            phonenumber="+989034488755"
        )
        self.category = Category.objects.create(category="نان بربری", box_color="red")
        self.category2 = Category.objects.create(category="2نان بربری", box_color="red")
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        self.product = Product.objects.create(
            name="Test Bread",
            price=10000,
            discount=10,
            category=self.category,
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
        product = Product.objects.create(name="Bread", price=100, discount=0, box_type=1, category=self.category)
        CartItem.objects.create(user=self.user, product=product, quantity=2)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_discount"], 0)
        self.assertEqual(response.data["total_actual_price"], 200)
        self.assertEqual(response.data["counts"], 1)

    def test_cart_with_discounted_item(self):
        """Cart item with 10% discount"""
        product = Product.objects.create(name="Bread", price=100, discount=10, box_type=1, category=self.category)
        CartItem.objects.create(user=self.user, product=product, quantity=3)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["total_discount"], 30)  # 3 * (100*10%)
        self.assertEqual(response.data["total_actual_price"], 270)

    def test_cart_with_multiple_items(self):
        """Cart with multiple products with and without discount"""
        p1 = Product.objects.create(name="A", price=100, discount=10, box_type=1, category=self.category)
        p2 = Product.objects.create(name="B", price=200, discount=0, box_type=2, category=self.category2)
        CartItem.objects.create(user=self.user, product=p1, quantity=2)  # 200 - 20
        CartItem.objects.create(user=self.user, product=p2, quantity=1)  # 200
        response = self.client.get(self.url)
        self.assertEqual(response.data["total_discount"], 20)
        self.assertEqual(response.data["total_actual_price"], 380)
        self.assertEqual(response.data["counts"], 2)

    def test_cart_with_valid_delivery(self):
        """Cart with valid delivery slot"""
        product = Product.objects.create(name="Bread", price=100, discount=0, box_type=1, category=self.category)
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
        product = Product.objects.create(name="Bread", price=100, discount=0, box_type=1, category=self.category)
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
        product = Product.objects.create(name="Bread", price=100, discount=0, box_type=1, category=self.category)
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
        self.category = Category.objects.create(category="نان بربری", box_color="red")
        self.category2 = Category.objects.create(category="2نان بربری", box_color="red")
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        self.product = Product.objects.create(
            name="Test Bread",
            price=10000,
            discount=10,
            category=self.category,
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
        self.category = Category.objects.create(category="نان بربری", box_color="red")
        self.category2 = Category.objects.create(category="2نان بربری", box_color="red")
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        self.product = Product.objects.create(
            name="Test Product",
            price=20000,
            discount=5,
            category=self.category,
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
        self.category = Category.objects.create(category="نان بربری", box_color="red")
        self.category2 = Category.objects.create(category="2نان بربری", box_color="red")
        self.product = Product.objects.create(
            name="Test Bread", price=10000, discount=0, category=self.category, box_type=1
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
        self.category = Category.objects.create(category="نان بربری", box_color="red")
        self.category2 = Category.objects.create(category="2نان بربری", box_color="red")
        self.product1 = Product.objects.create(
            name="Bread A", price=10000, discount=0, category=self.category, box_type=1
        )
        self.product2 = Product.objects.create(
            name="Bread B", price=20000, discount=5, category=self.category2, box_type=2
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
