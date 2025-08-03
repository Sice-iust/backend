from django.contrib import admin
from django.urls import path
from .views import *

urlpatterns = [
    path("user/tickets/", TicketView.as_view()),
    path("user/tickets/single/<int:id>/", SingleTicketView.as_view()),
    path("user/tickets/single/check/<int:id>/", PatchTicketView.as_view()),
    path("nanzi/admin/tickets/", AdminTicketView.as_view()),
    path("nanzi/admin/tickets/single/<int:id>/", AdminSingleTicketView.as_view()),
    path('nanzi/admin/ticket/list/',TicketListView.as_view()),
]
