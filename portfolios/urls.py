from django.contrib import admin
from django.urls import path,include
from . import views,models

from . import views

app_name = 'portfolios'

urlpatterns = [
    path('', views.PortfolioListView.as_view(), name='list'),
    path('create/', views.PortfolioCreate.as_view(), name='create'),
    path('delete/<pk>/', views.PortfolioDeleteView.as_view(), name='delete'),
    path('detail/<pk>/', views.PortfolioDetailView.as_view(), name='detail'),
    path('manage/<pk>/', views.manage_portfolios, name='manage'),
    path('rentabilidade/<pk>/', views.rentabilidade_portofolio, name='rentabilidade'),
    path('resumo/<pk>/', views.portfolio_resumo, name='resumo'),


    # AJAX calls for js renders
    path('autocomplete/', views.AtivoAutoComplete.as_view(), name='ativo-autocomplete' ),
]
