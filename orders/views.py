from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Order, OrderItem
from .forms import CheckoutForm
from .telegram import send_order_notification, send_cancel_notification
from cart.models import Cart


@login_required
def checkout(request):
    cart = get_object_or_404(Cart, user=request.user)
    form = CheckoutForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        order = Order.objects.create(
            user=request.user,
            full_name=form.cleaned_data['full_name'],
            email=form.cleaned_data['email'],
            phone=form.cleaned_data['phone'],
            address=form.cleaned_data['address'],
            total_price=cart.get_total_price(),
        )
        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                price=item.product.price,
                quantity=item.quantity,
            )
        cart.items.all().delete()
        send_order_notification(order)
        return redirect('/accounts/profile/?order_placed=1')
    return render(request, 'orders/checkout.html', {'cart': cart, 'form': form})


@login_required
def order_history(request):
    orders = request.user.orders.all()
    return render(request, 'orders/history.html', {'orders': orders})


@login_required
def order_detail(request, pk):
    order = get_object_or_404(Order, pk=pk, user=request.user)
    return render(request, 'orders/detail.html', {
        'order': order,
        'is_new': request.GET.get('new') == '1',
    })


@login_required
def cancel_order(request, pk):
    if request.method != 'POST':
        return redirect('orders:detail', pk=pk)
    order = get_object_or_404(Order, pk=pk, user=request.user)
    if order.status in ('pending', 'processing'):
        for item in order.items.select_related('product'):
            product = item.product
            product.stock += item.quantity
            if product.availability_status == 'out_of_stock' and product.stock > 0:
                product.availability_status = 'in_stock'
            product.save(update_fields=['stock', 'availability_status'])
        order.status = 'cancelled'
        order.save()
        send_cancel_notification(order)
    next_url = request.POST.get('next')
    if next_url:
        return redirect(next_url)
    return redirect('orders:detail', pk=pk)
