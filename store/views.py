from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Product, Category, Favourite
from orders.models import Order, OrderItem
from orders.telegram import send_order_notification

PLACEHOLDER_CATEGORIES = [
    {'name': 'Пазлы',               'sub': 'Классические пазлы',    'count': 100, 'icon': '🧩'},
    {'name': '3D пазлы',            'sub': 'Объёмные модели',        'count': 45,  'icon': '🏗️'},
    {'name': 'Деревянные игрушки',  'sub': 'Экологичные игрушки',   'count': 30,  'icon': '🪆'},
    {'name': 'Настольные игры',     'sub': 'Для всей семьи',        'count': 120, 'icon': '🎲'},
    {'name': 'Развивающие игрушки', 'sub': 'Для возраста через игру','count': 60, 'icon': '🎯'},
    {'name': 'Аксессуары',          'sub': 'Рамки и клей и пазлы',  'count': 40,  'icon': '🎁'},
]

PLACEHOLDER_PRODUCTS = [
    {'name': 'Горная панорама',    'category': 'Пазлы',             'price': '$29.99', 'icon': '🏔️'},
    {'name': '3D пазл «Механизм»', 'category': '3D пазлы',          'price': '$44.99', 'icon': '⚙️'},
    {'name': 'Цветная абстракция', 'category': 'Пазлы',             'price': '$24.99', 'icon': '🎨'},
    {'name': 'Деревянная машинка', 'category': 'Деревянные игрушки','price': '$19.99', 'icon': '🚗'},
]


@require_POST
@login_required
def toggle_favourite(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    fav, created = Favourite.objects.get_or_create(user=request.user, product=product)
    if not created:
        fav.delete()
        return JsonResponse({'status': 'removed'})
    return JsonResponse({'status': 'added'})


DELIVERY_THRESHOLD = 3
DELIVERY_COST = 10

@login_required
def favourites(request):
    items = Favourite.objects.filter(user=request.user).select_related('product__category')
    subtotal = sum(item.get_total_price() for item in items)
    count = sum(item.quantity for item in items)
    delivery = 0 if count >= DELIVERY_THRESHOLD else DELIVERY_COST
    grand_total = subtotal + delivery
    return render(request, 'store/favourites.html', {
        'items': items,
        'subtotal': subtotal,
        'count': count,
        'delivery': delivery,
        'grand_total': grand_total,
        'delivery_threshold': DELIVERY_THRESHOLD,
        'delivery_cost': DELIVERY_COST,
    })


@require_POST
@login_required
def favourite_update_qty(request, fav_id):
    fav = get_object_or_404(Favourite, pk=fav_id, user=request.user)
    action = request.POST.get('action')
    if action == 'inc':
        fav.quantity += 1
        fav.save()
    elif action == 'dec' and fav.quantity > 1:
        fav.quantity -= 1
        fav.save()
    return JsonResponse({'status': 'ok', 'quantity': fav.quantity,
                         'item_total': str(fav.get_total_price())})


@require_POST
@login_required
def favourite_remove(request, fav_id):
    fav = get_object_or_404(Favourite, pk=fav_id, user=request.user)
    fav.delete()
    return JsonResponse({'status': 'removed'})


@require_POST
@login_required
def quick_checkout(request):
    from decimal import Decimal
    product_id = request.POST.get('product_id')
    quantity = max(1, int(request.POST.get('quantity', 1)))
    product = get_object_or_404(Product, pk=product_id)

    profile = request.user.profile
    subtotal = product.price * quantity
    delivery = Decimal('0') if quantity >= DELIVERY_THRESHOLD else Decimal(str(DELIVERY_COST))
    total = subtotal + delivery

    address_parts = [p for p in [profile.city, profile.address] if p]
    address = ', '.join(address_parts) or '—'

    order = Order.objects.create(
        user=request.user,
        full_name=request.user.username,
        email=request.user.email or '',
        phone=profile.phone or '',
        address=address,
        total_price=total,
    )
    OrderItem.objects.create(
        order=order,
        product=product,
        price=product.price,
        quantity=quantity,
    )
    send_order_notification(order)
    return JsonResponse({'status': 'ok', 'order_id': order.pk})


@require_POST
@login_required
def favourites_checkout(request):
    items = list(Favourite.objects.filter(user=request.user).select_related('product'))
    if not items:
        return JsonResponse({'error': 'empty'}, status=400)

    profile = request.user.profile
    count = sum(i.quantity for i in items)
    subtotal = sum(i.get_total_price() for i in items)
    delivery = 0 if count >= DELIVERY_THRESHOLD else DELIVERY_COST
    total = subtotal + delivery

    address_parts = [p for p in [profile.city, profile.address] if p]
    address = ', '.join(address_parts) or '—'

    order = Order.objects.create(
        user=request.user,
        full_name=request.user.username,
        email=request.user.email or '',
        phone=profile.phone or '',
        address=address,
        total_price=total,
    )
    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            price=item.product.price,
            quantity=item.quantity,
        )
    Favourite.objects.filter(user=request.user).delete()
    send_order_notification(order)
    return JsonResponse({'status': 'ok', 'order_id': order.pk})


def product_list(request):
    categories = Category.objects.all()
    q = request.GET.get('q', '').strip()[:200]
    products = Product.objects.filter(available=True)
    if q:
        products = products.filter(name__icontains=q)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    fav_ids = set()
    if request.user.is_authenticated:
        fav_ids = set(Favourite.objects.filter(user=request.user).values_list('product_id', flat=True))

    db_has_products = Product.objects.filter(available=True).exists() if q else products.exists()

    return render(request, 'store/product_list.html', {
        'categories': categories,
        'page_obj': page_obj,
        'placeholder_categories': PLACEHOLDER_CATEGORIES if not categories.exists() else [],
        'placeholder_products': PLACEHOLDER_PRODUCTS if not db_has_products and not q else [],
        'search_query': q,
        'search_no_results': bool(q and not products.exists()),
        'fav_ids': fav_ids,
        'delivery_cost': DELIVERY_COST,
        'delivery_threshold': DELIVERY_THRESHOLD,
    })


def category_detail(request, slug):
    category = get_object_or_404(Category, slug=slug)
    products = category.products.filter(available=True)

    paginator = Paginator(products, 12)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    fav_ids = set()
    if request.user.is_authenticated:
        fav_ids = set(Favourite.objects.filter(user=request.user).values_list('product_id', flat=True))

    return render(request, 'store/category_detail.html', {
        'category': category,
        'page_obj': page_obj,
        'fav_ids': fav_ids,
        'delivery_cost': DELIVERY_COST,
        'delivery_threshold': DELIVERY_THRESHOLD,
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, available=True)
    fav_ids = set()
    if request.user.is_authenticated:
        fav_ids = set(Favourite.objects.filter(user=request.user).values_list('product_id', flat=True))
    return render(request, 'store/product_detail.html', {
        'product': product,
        'fav_ids': fav_ids,
        'delivery_cost': DELIVERY_COST,
        'delivery_threshold': DELIVERY_THRESHOLD,
    })
