from django.contrib import admin
from django.urls import path,include
from . import views


app_name = 'sysManager'

urlpatterns = [
    path('check_cargas/', views.CargasListView.as_view(), name='check_cargas'),

]
