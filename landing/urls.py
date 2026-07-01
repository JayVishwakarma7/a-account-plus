from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    path('', views.index, name='index'),
    path('contact-submit/', views.index, name='contact_submit'),
    path('clientmail/', views.clientmail, name='clientmail'),
]