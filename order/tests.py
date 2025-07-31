from django.test import TestCase
from rest_framework.exceptions import ValidationError
from users.models import Location
from product.models import Category, Product
from cart.models import CartItem, DeliveryCart
from order.models import *
from order.serializers import (
    UserSerializer,
    UserDiscountSerializer,
    LocationSerializer,
    DeliverySlotSerializer,
    DeliverySlotsByDaySerializer,
    FinalizeOrderSerializer,
    MyOrderSerializer,
    MyOrderItemSerializer,
    OrderInvoiceSerializer,
    AdminCancelSerializer,
    AdminArchiveSerializer,
    StatusSerializer,
    OrderIdSerializer,
)
from django.contrib.auth import get_user_model
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory
import datetime
import pytz
from django.utils import timezone
from decimal import Decimal
from datetime import time, timedelta
from order.filters import OrderFilter

User = get_user_model()


class SerializerTestCase(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            username="testuser",
            phonenumber="+989123456789",
            password="testpass",
            email="fatimaa@gmail.com",
        )
        self.category = Category.objects.create(category="نان", box_color="red")
        self.product = Product.objects.create(
            category=self.category,
            name="Test Product",
            price=100.0,
            description="Test desc",
            photo="test.jpg",
            stock=5,
            box_type=1,
            average_rate=4.5,
            discount=10,
            color="red",
        )
        self.location = Location.objects.create(
            user=self.user,
            name="خانه",
            address="Test Address",
            home_floor=2,
            home_unit=1,
            home_plaque=10,
            is_choose=True,
        )
        self.delivery_slot = DeliverySlots.objects.create(
            start_time="10:00:00",
            end_time="12:00:00",
            delivery_date=datetime.date.today(),
            max_orders=10,
            current_fill=5,
            shipping_fee=15.0,
        )
        self.order = Order.objects.create(
            user=self.user,
            location=self.location,
            delivery=self.delivery_slot,
            total_price=200,
            status=1,
            profit=20,
            description="desc",
            reciver="Ali",
            reciver_phone="09121112222",
            is_admin_canceled=False,
            admin_reason="",
            is_archive=False,
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            product_discount=5,
        )

    def test_user_serializer(self):
        serializer = UserSerializer(self.user)
        data = serializer.data
        self.assertEqual(data["username"], self.user.username)
        self.assertEqual(data["phonenumber"], self.user.phonenumber)

    def test_user_discount_serializer(self):
        serializer = UserDiscountSerializer(self.user)
        self.assertEqual(serializer.data["phonenumber"], self.user.phonenumber)

    def test_location_serializer(self):
        serializer = LocationSerializer(self.location)
        data = serializer.data
        self.assertEqual(data["name"], self.location.name)
        self.assertEqual(data["user"]["username"], self.user.username)

    def test_delivery_slot_serializer(self):
        serializer = DeliverySlotSerializer(self.delivery_slot)
        data = serializer.data
        self.assertIn("day_name", data)
        self.assertIn(
            data["day_name"],
            ["شنبه", "یک‌شنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"],
        )

    def test_delivery_slots_by_day_serializer(self):
        data = {
            "delivery_date": datetime.date.today(),
            "slots": [DeliverySlotSerializer(self.delivery_slot).data],
        }
        serializer = DeliverySlotsByDaySerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_finalize_order_serializer_valid(self):
        # We mock the request and cart_info to simulate cart info presence
        request = self.factory.post("/fake-url/")
        request.user = self.user
        serializer_context = {"request": request}

        data = {
            "location_id": self.location.id,
            "deliver_time": 1,
            "description": "",
            "total_price": "0",  # Will be overwritten
            "profit": "0",  # Will be overwritten
            "total_payment": "0",  # Will be overwritten
            "reciver": "Ali",
            "reciver_phone": "09121112222",
        }

        # Patch cart_info function to return sample cart info
        from order import serializers as order_serializers

        def mock_cart_info(req):
            return {
                "total_discount": 5,
                "total_actual_price_with_shipp": 105,
            }

        order_serializers.cart_info = mock_cart_info

        serializer = FinalizeOrderSerializer(data=data, context=serializer_context)
        self.assertTrue(serializer.is_valid())
        validated = serializer.validated_data
        self.assertEqual(float(validated["profit"]), 5)
        self.assertEqual(float(validated["total_price"]), 105)
        self.assertEqual(validated["payment_status"], "unpaid")

    def test_finalize_order_serializer_empty_cart(self):
        request = self.factory.post("/fake-url/")
        request.user = self.user
        serializer_context = {"request": request}

        data = {
            "location_id": self.location.id,
            "deliver_time": 1,
            "description": "",
            "total_price": "0",
            "profit": "0",
            "total_payment": "0",
            "reciver": "Ali",
            "reciver_phone": "09121112222",
        }

        from order import serializers as order_serializers

        def mock_cart_info_empty(req):
            return {}

        order_serializers.cart_info = mock_cart_info_empty

        serializer = FinalizeOrderSerializer(data=data, context=serializer_context)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_my_order_serializer(self):
        serializer = MyOrderSerializer(self.order)
        data = serializer.data
        self.assertEqual(data["id"], self.order.id)
        self.assertEqual(data["location"]["name"], self.location.name)
        self.assertEqual(data["delivery"]["id"], self.delivery_slot.id)

    def test_my_order_item_serializer(self):
        request = self.factory.get("/")
        serializer = MyOrderItemSerializer(self.order_item, context={"request": request})
        data = serializer.data
        self.assertEqual(data["quantity"], self.order_item.quantity)
        self.assertEqual(data["product"]["name"], self.product.name)
        self.assertEqual(data["order"]["id"], self.order.id)


    def test_order_invoice_serializer(self):
        request = self.factory.get("/")
        serializer = OrderInvoiceSerializer(self.order_item, context={"request": request})
        data = serializer.data
        self.assertEqual(data["quantity"], self.order_item.quantity)
        self.assertEqual(data["product"]["name"], self.product.name)

    def test_admin_cancel_serializer(self):
        data = {"order_id": self.order.id, "reason": "test reason"}
        serializer = AdminCancelSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_admin_archive_serializer(self):
        data = {"order_id": self.order.id}
        serializer = AdminArchiveSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_status_serializer(self):
        data = {"order_id": self.order.id, "status": 2}
        serializer = StatusSerializer(data=data)
        self.assertTrue(serializer.is_valid())

    def test_order_id_serializer(self):
        serializer = OrderIdSerializer(self.order)
        self.assertEqual(serializer.data["id"], self.order.id)


class OrderModelsTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", phonenumber="+989123456789", password="testpass",email="sraa@gmail.com"
        )
        self.category = Category.objects.create(category="نان", box_color="red")
        self.product = Product.objects.create(
            category=self.category,
            name="نان تست",
            price=Decimal("100.00"),
            description="توضیح تست",
            photo="path/to/photo.jpg",
            stock=10,
            box_type=1,
            average_rate=0,
            discount=10,
            color="brown",
        )
        self.location = Location.objects.create(
            user=self.user,
            name="خانه",
            address="آدرس تست",
            home_floor=1,
            home_unit=2,
            home_plaque=3,
        )
        self.delivery_slot = DeliverySlots.objects.create(
            start_time="10:00:00",
            end_time="12:00:00",
            delivery_date=timezone.now().date() + timedelta(days=1),
            max_orders=5,
            current_fill=0,
            shipping_fee=Decimal("10.00"),
        )
        self.discount_cart = DiscountCart.objects.create(
            user=self.user,
            text="DISCOUNT10",
            percentage=10,
            max_discount=Decimal("50.00"),
            max_use=5,
            payment_without_discount=Decimal("100.00"),
            product=self.product,
        )

    def test_discount_cart_str(self):
        self.assertEqual(
            str(self.discount_cart), f"DISCOUNT10 - 10% for {self.user.username}"
        )

    def test_order_str_and_save_delivered_at(self):
        order = Order.objects.create(
            user=self.user,
            location=self.location,
            delivery=self.delivery_slot,
            total_price=Decimal("200.00"),
            profit=Decimal("20.00"),
            status=4,  
            reciver="Ali",
            reciver_phone="09121112222",
        )
        
        self.assertIsNotNone(order.delivered_at)
        self.assertIn(str(self.user.phonenumber), str(order))
        order.status = 1
        order.save()
        self.assertIsNone(order.delivered_at)

    def test_order_item_str(self):
        order = Order.objects.create(
            user=self.user,
            location=self.location,
            delivery=self.delivery_slot,
        )
        order_item = OrderItem.objects.create(
            order=order,
            product=self.product,
            quantity=3,
            product_discount=5,
        )
        expected_str = f"3 x {self.product.name} (Order #{order.id})"
        self.assertEqual(str(order_item), expected_str)

    def test_delivery_slots_fields(self):
        self.assertEqual(self.delivery_slot.max_orders, 5)
        self.assertEqual(self.delivery_slot.current_fill, 0)
        self.assertEqual(self.delivery_slot.shipping_fee, Decimal("10.00"))

    def test_discount_cart_constraints(self):
        self.discount_cart.percentage = 101
        with self.assertRaises(Exception):
            self.discount_cart.full_clean()

        self.discount_cart.percentage = -1
        with self.assertRaises(Exception):
            self.discount_cart.full_clean()

        self.discount_cart.percentage = 50
        try:
            self.discount_cart.full_clean()
        except Exception:
            self.fail("DiscountCart with valid percentage should not raise error.")


class OrderFilterTestCase(TestCase):
    def setUp(self):
        # ایجاد کاربر، دسته‌بندی، محصول، محل و زمان تحویل
        self.user = User.objects.create_user(
            username="testuser",
            phonenumber="+989123456789",
            password="testpass",email="fatat@gmail.com"
        )
        self.category = Category.objects.create(category="نان", box_color="red")
        self.product = Product.objects.create(
            category=self.category,
            name="نان تست",
            price=100,
            description="توضیح تست",
            photo="path/to/photo.jpg",
            stock=10,
            box_type=1,
            average_rate=0,
            discount=0,
            color="brown",
        )
        self.location = Location.objects.create(
            user=self.user,
            name="خانه",
            address="آدرس تست",
            home_floor=1,
            home_unit=2,
            home_plaque=3,
        )
        self.delivery1 = DeliverySlots.objects.create(
            start_time=time(10, 0),
            end_time=time(12, 0),
            delivery_date=timezone.now().date(),
            max_orders=5,
            current_fill=0,
            shipping_fee=10,
        )
        self.delivery2 = DeliverySlots.objects.create(
            start_time=time(14, 0),
            end_time=time(16, 0),
            delivery_date=timezone.now().date() + timedelta(days=1),
            max_orders=5,
            current_fill=0,
            shipping_fee=10,
        )
        # ایجاد سفارش‌ها
        self.order1 = Order.objects.create(
            user=self.user,
            location=self.location,
            delivery=self.delivery1,
            total_price=100,
            profit=10,
            status=1,
            is_archive=False,
            is_admin_canceled=False,
        )
        self.order2 = Order.objects.create(
            user=self.user,
            location=self.location,
            delivery=self.delivery2,
            total_price=200,
            profit=20,
            status=2,
            is_archive=True,
            is_admin_canceled=True,
        )

    def test_filter_by_delivery_date(self):
        data = {"delivery_date": timezone.now().date()}
        filtered = OrderFilter(data, queryset=Order.objects.all())
        self.assertIn(self.order1, filtered.qs)
        self.assertNotIn(self.order2, filtered.qs)

    def test_filter_by_delivery_date_range(self):
        data = {
            "delivery_date__gte": timezone.now().date(),
            "delivery_date__lte": timezone.now().date(),
        }
        filtered = OrderFilter(data, queryset=Order.objects.all())
        self.assertIn(self.order1, filtered.qs)
        self.assertNotIn(self.order2, filtered.qs)

    def test_filter_by_is_archive(self):
        data = {"is_archive": True}
        filtered = OrderFilter(data, queryset=Order.objects.all())
        self.assertIn(self.order2, filtered.qs)
        self.assertNotIn(self.order1, filtered.qs)

    def test_filter_by_is_admin_canceled(self):
        data = {"is_admin_canceled": True}
        filtered = OrderFilter(data, queryset=Order.objects.all())
        self.assertIn(self.order2, filtered.qs)
        self.assertNotIn(self.order1, filtered.qs)

    def test_filter_by_id(self):
        data = {"id": self.order1.id}
        filtered = OrderFilter(data, queryset=Order.objects.all())
        self.assertIn(self.order1, filtered.qs)
        self.assertNotIn(self.order2, filtered.qs)

    def test_filter_by_start_time_gte(self):
        data = {"start_time__gte": time(9, 0)}
        filtered = OrderFilter(data, queryset=Order.objects.all())
        self.assertIn(self.order1, filtered.qs)

        data = {"start_time__gte": time(15, 0)}
        filtered = OrderFilter(data, queryset=Order.objects.all())
        self.assertNotIn(self.order1, filtered.qs)
        self.assertIn(self.order2, filtered.qs)

    def test_filter_by_end_time_lte(self):
        data = {"end_time__lte": time(13, 0)}
        filtered = OrderFilter(data, queryset=Order.objects.all())
        self.assertIn(self.order1, filtered.qs)
        self.assertNotIn(self.order2, filtered.qs)
