from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db import IntegrityError, transaction
from .forms import RegisterForm, AddressForm
from .models import UserProfile


def user_login(request):
    next_url = request.GET.get('next') or request.POST.get('next') or 'store:product_list'
    error = None
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url)
        error = 'Неверное имя пользователя или пароль.'
    return render(request, 'accounts/login.html', {'error': error, 'next': next_url})


def check_email(request):
    email = request.GET.get('email', '').strip().lower()
    if not email or '@' not in email:
        return JsonResponse({'valid': False, 'message': 'Введите корректный email'})

    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse({'valid': False, 'message': 'Этот email уже зарегистрирован'})

    return JsonResponse({'valid': True})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    user = User.objects.create_user(
                        username=form.cleaned_data['username'],
                        email=form.cleaned_data['email'].lower(),
                        password=form.cleaned_data['password1'],
                    )
                    user.profile.phone = form.cleaned_data.get('phone', '')
                    user.profile.save()
                login(request, user)
                return redirect('store:product_list')
            except IntegrityError:
                form.add_error('username', 'Это имя пользователя уже занято.')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    orders = request.user.orders.prefetch_related('items__product').all()
    total_orders     = orders.count()
    pending_orders   = orders.filter(status__in=['pending', 'processing']).count()
    shipped_orders   = orders.filter(status='shipped').count()
    delivered_orders = orders.filter(status='delivered').count()
    cancelled_orders = orders.filter(status='cancelled').count()

    profile_errors = {}
    if request.method == 'POST' and 'save_profile' in request.POST:
        new_username = request.POST.get('username', '').strip()
        new_phone = request.POST.get('phone', '').strip()

        if not new_username:
            profile_errors['username'] = 'Имя пользователя не может быть пустым'
        elif User.objects.exclude(pk=request.user.pk).filter(username=new_username).exists():
            profile_errors['username'] = 'Это имя уже занято'

        if not profile_errors:
            request.user.username = new_username
            request.user.save()
            profile.phone = ('+992' + new_phone) if new_phone and not new_phone.startswith('+') else new_phone
            profile.save()
            return redirect('accounts:profile')

    if request.method == 'POST' and 'save_address' in request.POST:
        address_form = AddressForm(request.POST, instance=profile)
        if address_form.is_valid():
            address_form.save()
            return redirect('accounts:profile')
    else:
        address_form = AddressForm(instance=profile)

    return render(request, 'accounts/profile.html', {
        'orders': orders[:10],
        'total_orders':     total_orders,
        'pending_orders':   pending_orders,
        'shipped_orders':   shipped_orders,
        'delivered_orders': delivered_orders,
        'cancelled_orders': cancelled_orders,
        'address_form': address_form,
        'profile_errors': profile_errors,
    })
