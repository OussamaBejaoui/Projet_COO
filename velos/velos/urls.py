"""
URL configuration for velos project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
from high_level import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("pays/<int:pk>/", views.PaysDetailView.as_view()),
    path("ville/<int:pk>/", views.VilleDetailView.as_view()),
    path("machine/<int:pk>/", views.MachineDetailView.as_view()),
    path("quantitemachine/<int:pk>/", views.QuantiteMachineDetailView.as_view()),
    path("lieu/<int:pk>/", views.LieuDetailView.as_view()),
    path("transport/<int:pk>/", views.TransportDetailView.as_view()),
    path("operation/<int:pk>/", views.OperationDetailView.as_view()),
    path("produit/<int:pk>/", views.ProduitDetailView.as_view()),
    path("prixproduit/<int:pk>/", views.PrixProduitDetailView.as_view()),
    path("fournisseur/<int:pk>/", views.FournisseurDetailView.as_view()),
    path("quantiteproduit/<int:pk>/", views.QuantiteProduitDetailView.as_view()),
    path("stock/<int:pk>/", views.StockDetailView.as_view()),
    path("pointdevente/<int:pk>/", views.PointDeVenteDetailView.as_view()),
    path("facture/<int:pk>/", views.FactureDetailView.as_view()),
    path("api/<int:pk>", views.ApiView.as_view()),
]
