from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Ticket
from .serializers import (
    TicketSerializer,
    AdminTicketSerializer,
    PatchAdminSerializer,
    PatchUserSerializer,
)
from django.shortcuts import get_object_or_404
from order.models import Order
from rest_framework.filters import OrderingFilter
from users.permissions import IsAdminGroupUser

class TicketView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSerializer

    def get(self, request):
        tickets = Ticket.objects.filter(user=request.user)
        serializer = self.serializer_class(tickets, many=True)
        return Response(serializer.data)

    def post(self, request):
        order_id = request.data.get('order_id')
        if not order_id:
            return Response({"order_id": "This field is required."}, status=status.HTTP_400_BAD_REQUEST)

        order = get_object_or_404(Order, id=order_id)
        if order.user != request.user:
            return Response({"detail": "You do not have permission to create a ticket for this order."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user, order=order)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SingleTicketView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TicketSerializer
    def put(self, request, id):
        ticket = get_object_or_404(Ticket, id=id, user=request.user)
        serializer = self.serializer_class(ticket, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        ticket = get_object_or_404(Ticket, id=id, user=request.user)
        ticket.delete()
        return Response(
            {"detail": "Ticket deleted successfully."},
            status=status.HTTP_204_NO_CONTENT,
        )
class PatchTicketView(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = PatchUserSerializer
    def patch(self, request, id):
        try:
            ticket = Ticket.objects.get(id=id, user=request.user)
        except Ticket.DoesNotExist:
            return Response(
                {"message": "Ticket not found or not owned by you"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if "is_close" not in request.data:
            return Response(
                {"message": "'is_close' field is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = TicketSerializer(
            ticket, data={"is_close": request.data["is_close"]}, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AdminTicketView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    serializer_class = AdminTicketSerializer

    def get(self, request):

        tickets = Ticket.objects.all().order_by("-created_at")
        serializer = self.serializer_class(tickets, many=True)
        return Response(serializer.data)


class AdminSingleTicketView(APIView):
    permission_classes = [IsAuthenticated, IsAdminGroupUser]
    serializer_class = PatchAdminSerializer

    def patch(self, request, id):
        try:
            ticket = Ticket.objects.get(id=id)
        except Ticket.DoesNotExist:
            return Response(
                {"message": "Ticket not found"}, status=status.HTTP_404_NOT_FOUND
            )

        updated = False

        if "admin_check" in request.data:
            ticket.admin_check = request.data["admin_check"]
            updated = True

        if "admin_answer" in request.data:
            ticket.admin_answer = request.data["admin_answer"]
            updated = True

        if updated:
            ticket.save()
            return Response(TicketSerializer(ticket).data, status=status.HTTP_200_OK)

        return Response(
            {"message": "No valid fields to update"}, status=status.HTTP_400_BAD_REQUEST
        )
