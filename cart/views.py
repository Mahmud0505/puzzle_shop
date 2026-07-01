from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from store.models import Product
from .models import Cart, CartItem


@login_required
def cart_detail(request):
    cart, _ = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart/detail.html', {'cart': cart})


@login_required
def cart_add(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created and item.quantity < product.stock:
        item.quantity += 1
        item.save()
    return redirect('cart:detail')


@login_required
def cart_remove(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    item.delete()
    return redirect('cart:detail')


@require_POST
@login_required
def cart_update_qty(request, item_id):
    item = get_object_or_404(CartItem, pk=item_id, cart__user=request.user)
    action = request.POST.get('action')
    stock = item.product.stock

    if action == 'inc':
        if item.quantity >= stock:
            return JsonResponse({
                'status': 'stock_limit',
                'quantity': item.quantity,
                'stock': stock,
                'item_total': str(item.get_total_price()),
                'cart_total': str(item.cart.get_total_price()),
            })
        item.quantity += 1
        item.save()
    elif action == 'dec':
        if item.quantity > 1:
            item.quantity -= 1
            item.save()

    return JsonResponse({
        'status': 'ok',
        'quantity': item.quantity,
        'stock': stock,
        'item_total': str(item.get_total_price()),
        'cart_total': str(item.cart.get_total_price()),
    })
