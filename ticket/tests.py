from django.test import TestCase
from django.contrib.auth import get_user_model
from order.models import Order,DeliverySlots
from .models import Ticket
from users.models import Location
User = get_user_model()
from datetime import time, timedelta, datetime,date
import datetime
from ticket.serializers import (
    TicketSerializer,
    AdminTicketSerializer,
    PatchAdminSerializer,
    PatchUserSerializer,
)

class TicketModelTest(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="testuser", password="password123",email="asdfg@gmail.com",phonenumber="+989034456677"
        )

        self.admin_user = User.objects.create_user(
            username="adminuser", password="password123",email="sdfg@gmail.com",phonenumber="+989999999999"
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
        self.ticket = Ticket.objects.create(
            user=self.user,
            order=self.order,
            title="Test Ticket",
            description="Ticket description",
            category="technical",
        )
    def test_priority_auto_assignment(self):

        ticket = Ticket.objects.create(
            user=self.user,
            order=self.order,
            title="Technical Issue",
            description="Issue description",
            category="technical",
        )
        self.assertEqual(ticket.priority, "urgent")

        ticket = Ticket.objects.create(
            user=self.user,
            title="Payment Problem",
            description="Payment description",
            category="payment",
        )
        self.assertEqual(ticket.priority, "urgent")

        ticket = Ticket.objects.create(
            user=self.user,
            title="Public Question",
            description="Question description",
            category="public",
        )
        self.assertEqual(ticket.priority, "important")

        ticket = Ticket.objects.create(
            user=self.user,
            title="Suggestion Idea",
            description="Idea description",
            category="suggestions",
        )
        self.assertEqual(ticket.priority, "normal")

    def test_admin_fields_and_status_flags(self):
        ticket = Ticket.objects.create(
            user=self.user,
            order=self.order,
            title="Admin Test",
            description="Testing admin fields",
            category="technical",
        )

        self.assertIsNone(ticket.admin_user)
        self.assertFalse(ticket.admin_check)
        self.assertFalse(ticket.is_close)
        self.assertIsNone(ticket.admin_answer)

        ticket.admin_user = self.admin_user
        ticket.admin_answer = "Issue resolved"
        ticket.admin_check = True
        ticket.is_close = True
        ticket.save()

        updated_ticket = Ticket.objects.get(id=ticket.id)
        self.assertEqual(updated_ticket.admin_user, self.admin_user)
        self.assertEqual(updated_ticket.admin_answer, "Issue resolved")
        self.assertTrue(updated_ticket.admin_check)
        self.assertTrue(updated_ticket.is_close)

    def test_order_nullable(self):

        ticket = Ticket.objects.create(
            user=self.user,
            title="No Order Ticket",
            description="This ticket has no order",
            category="suggestions",
        )
        self.assertIsNone(ticket.order)

    def test_str_method(self):
        ticket = Ticket.objects.create(
            user=self.user,
            title="String Test",
            description="Check __str__",
            category="payment",
        )
        expected_str = f"{ticket.title} - {ticket.get_priority_display()}"
        self.assertEqual(str(ticket), expected_str)
    def test_ticket_serializer_read(self):
        serializer = TicketSerializer(instance=self.ticket)
        data = serializer.data
        self.assertEqual(data["title"], "Test Ticket")
        self.assertEqual(data["priority"], "urgent")
        self.assertEqual(data["order"]["id"], self.order.id)
        self.assertFalse(data["admin_check"])
        self.assertFalse(data["is_close"])

    def test_admin_ticket_serializer_read(self):
        serializer = AdminTicketSerializer(instance=self.ticket)
        data = serializer.data
        self.assertEqual(data["user"]["username"], "testuser")
        self.assertEqual(data["category"], "technical")
        self.assertEqual(data["order"]["id"], self.order.id)

    def test_patch_admin_serializer(self):
        data = {"admin_answer": "Issue solved", "admin_check": True}
        serializer = PatchAdminSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertEqual(serializer.validated_data["admin_answer"], "Issue solved")
        self.assertTrue(serializer.validated_data["admin_check"])

    def test_patch_user_serializer(self):
        data = {"is_close": True}
        serializer = PatchUserSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        self.assertTrue(serializer.validated_data["is_close"])


from rest_framework.test import APIClient
from django.contrib.auth.models import Group


class AdminTicketListViewTest(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="user1",
            password="pass123",
            email="user1@test.com",
            phonenumber="+989012345678",
        )
        self.admin = User.objects.create_user(
            username="admin1",
            password="pass123",
            email="admin1@test.com",
            phonenumber="+989087654321",
        )

        admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.admin.groups.add(admin_group)

        self.location = Location.objects.create(
            user=self.user,
            name="خانه",
            address="Address",
            home_floor=1,
            home_unit=2,
            home_plaque=5,
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
            total_price=100,
            status=1,
            profit=10,
            description="desc",
            reciver="Ali",
            reciver_phone="09121112222",
            is_admin_canceled=False,
            admin_reason="",
            is_archive=False,
        )

        self.ticket1 = Ticket.objects.create(
            user=self.user,
            order=self.order,
            title="Ticket 1",
            description="desc 1",
            category="technical",
        )
        self.ticket2 = Ticket.objects.create(
            user=self.user,
            order=self.order,
            title="Ticket 2",
            description="desc 2",
            category="payment",
        )
        self.ticket3 = Ticket.objects.create(
            user=self.user,
            order=self.order,
            title="Ticket 3",
            description="desc 3",
            category="public",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

    def test_list_all_tickets(self):
        response = self.client.get("/nanzi/admin/ticket/list/") 
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_filter_by_priority(self):

        response = self.client.get("/nanzi/admin/ticket/list/?priority=urgent")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)
        priorities = {ticket["priority"] for ticket in response.data}
        self.assertSetEqual(priorities, {"urgent"})

    def test_filter_by_category(self):
        response = self.client.get("/nanzi/admin/ticket/list/?category=public")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["category"], "public")

    def test_filter_by_priority_and_category(self):
        response = self.client.get("/nanzi/admin/ticket/list/?priority=urgent&category=payment")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["category"], "payment")
        self.assertEqual(response.data[0]["priority"], "urgent")


from rest_framework import status
from django.contrib.auth.models import Group
from django.urls import reverse


class AdminSingleTicketViewTest(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="user1",
            password="pass123",
            email="user1@test.com",
            phonenumber="+989012345678",
        )
        self.admin = User.objects.create_user(
            username="admin1",
            password="pass123",
            email="admin1@test.com",
            phonenumber="+989087654321",
        )

        admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.admin.groups.add(admin_group)

        self.location = Location.objects.create(
            user=self.user,
            name="خانه",
            address="Address",
            home_floor=1,
            home_unit=2,
            home_plaque=5,
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
            total_price=100,
            status=1,
            profit=10,
            description="desc",
            reciver="Ali",
            reciver_phone="09121112222",
            is_admin_canceled=False,
            admin_reason="",
            is_archive=False,
        )

        self.ticket = Ticket.objects.create(
            user=self.user,
            order=self.order,
            title="Test Ticket",
            description="Ticket description",
            category="technical",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.url = f"/nanzi/admin/tickets/single/{self.ticket.id}/"

    def test_patch_admin_check(self):
        response = self.client.patch(self.url, {"admin_check": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.admin_check)

    def test_patch_admin_answer(self):
        response = self.client.patch(
            self.url, {"admin_answer": "Issue resolved"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.admin_answer, "Issue resolved")

    def test_patch_both_fields(self):
        data = {"admin_check": True, "admin_answer": "Done"}
        response = self.client.patch(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.admin_check)
        self.assertEqual(self.ticket.admin_answer, "Done")

    def test_patch_no_valid_fields(self):
        response = self.client.patch(self.url, {"invalid_field": "x"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("No valid fields to update", response.content.decode())

    def test_patch_nonexistent_ticket(self):
        url = "/nanzi/admin/tickets/single/1234567/"
        response = self.client.patch(url, {"admin_check": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Ticket not found", response.data["message"])


class AdminTicketViewTest(TestCase):

    def setUp(self):

        self.user = User.objects.create_user(
            username="user1",
            password="pass123",
            email="user1@test.com",
            phonenumber="+989012345678",
        )
        self.admin = User.objects.create_user(
            username="admin1",
            password="pass123",
            email="admin1@test.com",
            phonenumber="+989087654321",
        )

        admin_group, _ = Group.objects.get_or_create(name="Admin")
        self.admin.groups.add(admin_group)

        self.location = Location.objects.create(
            user=self.user,
            name="خانه",
            address="Address",
            home_floor=1,
            home_unit=2,
            home_plaque=5,
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
            total_price=100,
            status=1,
            profit=10,
            description="desc",
            reciver="Ali",
            reciver_phone="09121112222",
            is_admin_canceled=False,
            admin_reason="",
            is_archive=False,
        )

        self.ticket1 = Ticket.objects.create(
            user=self.user,
            order=self.order,
            title="Ticket 1",
            description="desc 1",
            category="technical",
        )
        self.ticket2 = Ticket.objects.create(
            user=self.user,
            order=self.order,
            title="Ticket 2",
            description="desc 2",
            category="payment",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.admin)

        self.url = "/nanzi/admin/tickets/"

    def test_get_all_tickets_as_admin(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        titles = [ticket["title"] for ticket in response.data]
        self.assertIn("Ticket 1", titles)
        self.assertIn("Ticket 2", titles)

    def test_get_tickets_non_admin_forbidden(self):

        self.client.force_authenticate(user=self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class PatchTicketViewTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            username="user1",
            password="pass123",
            email="user1@test.com",
            phonenumber="+989012345678",
        )
        self.other_user = User.objects.create_user(
            username="user2",
            password="pass123",
            email="user2@test.com",
            phonenumber="+989087654321",
        )
        self.location = Location.objects.create(
            user=self.user,
            name="خانه",
            address="Address",
            home_floor=1,
            home_unit=2,
            home_plaque=5,
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
            total_price=100,
            status=1,
            profit=10,
            description="desc",
            reciver="Ali",
            reciver_phone="09121112222",
            is_admin_canceled=False,
            admin_reason="",
            is_archive=False,
        )
        self.ticket = Ticket.objects.create(
            user=self.user,
            order=self.order,
            title="Ticket 1",
            description="desc 1",
            category="technical",
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.url = f"/user/tickets/single/check/{self.ticket.id}/"

    def test_patch_is_close_success(self):
        response = self.client.patch(self.url, {"is_close": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.is_close)

    def test_patch_missing_is_close_field(self):
        response = self.client.patch(self.url, {"wrong_field": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("'is_close' field is required", response.content.decode())

    def test_patch_ticket_not_owned(self):
        self.client.force_authenticate(user=self.other_user)
        response = self.client.patch(self.url, {"is_close": True}, format="json")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("Ticket not found or not owned by you", response.content.decode())

    def test_patch_invalid_value(self):
        response = self.client.patch(
            self.url, {"is_close": "not_boolean"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
