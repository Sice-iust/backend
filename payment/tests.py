from django.test import TestCase

# Create your tests here.
from unittest.mock import patch, MagicMock
from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth import get_user_model
from decimal import Decimal
from .views import ZarinpalPayment
from .models import ZarinpalTransaction
import requests
User = get_user_model()

class ZarinpalPaymentTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            phonenumber='+989105406567',username="testuser", password="testpass", email="test@example.com"
        )
        self.gateway = ZarinpalPayment(callback_url="http://localhost/callback/")
        self.merchant_id = "test-merchant-id"
        self.amount = 10000
        self.description = "Test payment"

    @patch("payment.views.requests.post")
    def test_successful_payment_request(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"code": 100, "authority": "A000000"},
            "errors": []
        }
        mock_post.return_value = mock_response

        response = self.gateway.request(
            user=self.user,
            amount=self.amount,
            description=self.description,
            merchant_id=self.merchant_id,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("payment_url", response.data)
        self.assertTrue(response.data["payment_url"].startswith("https://sandbox.zarinpal.com/pg/StartPay/"))
        self.assertTrue(ZarinpalTransaction.objects.filter(authority="A000000").exists())

    @patch("payment.views.requests.post")
    def test_failed_payment_gateway_connection(self, mock_post):
        mock_post.side_effect = requests.RequestException("Connection error")

        response = self.gateway.request(
            user=self.user,
            amount=self.amount,
            description=self.description,
            merchant_id=self.merchant_id,
        )
        self.assertEqual(response.status_code, status.HTTP_503_SERVICE_UNAVAILABLE)
        self.assertIn("error", response.data)

    @patch("payment.views.requests.post")
    def test_unsuccessful_payment_request(self, mock_post):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.json.return_value = {"data": {"code": -1}, "errors": ["Invalid data"]}
        mock_post.return_value = mock_response

        response = self.gateway.request(
            user=self.user,
            amount=self.amount,
            description=self.description,
            merchant_id=self.merchant_id,
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch("payment.views.requests.post")
    def test_successful_verification(self, mock_post):
        transaction = ZarinpalTransaction.objects.create(
            user=self.user, authority="A12345", amount=self.amount, status="pending"
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"code": 100, "ref_id": "R123", "card_pan": "621986******0000"},
        }
        mock_post.return_value = mock_response

        response = self.gateway.verify(
            status_query="OK",
            authority="A12345",
            merchant_id=self.merchant_id,
            amount=self.amount,
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "completed")

    def test_verification_transaction_not_found(self):
        response = self.gateway.verify(
            status_query="OK",
            authority="INVALID",
            merchant_id=self.merchant_id,
            amount=self.amount,
        )
        self.assertEqual(response.status_code, 404)

    def test_verification_status_not_ok(self):
        transaction = ZarinpalTransaction.objects.create(
            user=self.user, authority="A54321", amount=self.amount, status="pending"
        )
        response = self.gateway.verify(
            status_query="NOK",
            authority="A54321",
            merchant_id=self.merchant_id,
            amount=self.amount,
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["status"], "failed")

    @patch("payment.views.requests.post")
    def test_verification_code_101(self, mock_post):
        transaction = ZarinpalTransaction.objects.create(
            user=self.user, authority="A101", amount=self.amount, status="pending"
        )
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "data": {"code": 101}
        }
        mock_post.return_value = mock_response

        response = self.gateway.verify(
            status_query="OK",
            authority="A101",
            merchant_id=self.merchant_id,
            amount=self.amount,
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("you submit later", response.data["message"])