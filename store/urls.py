from django.urls import path
from . import views

app_name = 'store'

urlpatterns = [
    path('', views.product_list, name='product_list'),
    path('category/<slug:slug>/', views.category_detail, name='category'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('favourite/toggle/<int:product_id>/', views.toggle_favourite, name='toggle_favourite'),
    path('favourites/', views.favourites, name='favourites'),
    path('quick-checkout/', views.quick_checkout, name='quick_checkout'),
    path('favourites/checkout/', views.favourites_checkout, name='favourites_checkout'),
    path('favourites/<int:fav_id>/qty/', views.favourite_update_qty, name='favourite_update_qty'),
    path('favourites/<int:fav_id>/remove/', views.favourite_remove, name='favourite_remove'),
]
