import random
import socket
import time

from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.http import JsonResponse
from django.db import IntegrityError
from .forms import RegisterForm, AddressForm
from .models import UserProfile


def check_email(request):
    """AJAX: проверяет формат и существование домена email."""
    email = request.GET.get('email', '').strip().lower()
    if not email or '@' not in email:
        return JsonResponse({'valid': False, 'message': 'Введите корректный email'})

    if User.objects.filter(email__iexact=email).exists():
        return JsonResponse({'valid': False, 'message': 'Этот email уже зарегистрирован'})

    try:
        domain = email.split('@')[1]
        socket.getaddrinfo(domain, None)
        return JsonResponse({'valid': True})
    except (socket.gaierror, IndexError):
        return JsonResponse({'valid': False, 'message': 'Такой email не существует'})


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            code = str(random.randint(100000, 999999))
            request.session['pending_reg'] = {
                'username': form.cleaned_data['username'],
                'email': form.cleaned_data['email'],
                'phone': form.cleaned_data.get('phone', ''),
                'password': form.cleaned_data['password1'],
            }
            request.session['email_code'] = code
            request.session['email_code_expires'] = time.time() + 600  # 10 минут

            send_mail(
                subject='Код подтверждения — Puzzle House',
                message=(
                    f'Привет, {form.cleaned_data["username"]}!\n\n'
                    f'Ваш код подтверждения: {code}\n\n'
                    'Код действителен 10 минут.\n\n'
                    'Если вы не регистрировались на Puzzle House — просто проигнорируйте это письмо.'
                ),
                from_email=None,
                recipient_list=[form.cleaned_data['email']],
                fail_silently=False,
            )
            return redirect('accounts:verify_email')
    else:
        form = RegisterForm()
    return render(request, 'accounts/register.html', {'form': form})


def verify_email(request):
    if 'pending_reg' not in request.session:
        return redirect('accounts:register')

    pending = request.session['pending_reg']
    error = None

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'resend':
            code = str(random.randint(100000, 999999))
            request.session['email_code'] = code
            request.session['email_code_expires'] = time.time() + 600
            send_mail(
                subject='Новый код подтверждения — Puzzle House',
                message=f'Ваш новый код подтверждения: {code}\n\nКод действителен 10 минут.',
                from_email=None,
                recipient_list=[pending['email']],
                fail_silently=False,
            )
            return render(request, 'accounts/verify_email.html', {
                'email': pending['email'],
                'resent': True,
            })

        attempts = request.session.get('verify_attempts', 0)
        if attempts >= 5:
            del request.session['pending_reg']
            request.session.pop('email_code', None)
            request.session.pop('email_code_expires', None)
            request.session.pop('verify_attempts', None)
            return render(request, 'accounts/verify_email.html', {
                'email': pending['email'],
                'error': 'Превышено количество попыток. Зарегистрируйтесь заново.',
                'expired': True,
            })

        entered = request.POST.get('code', '').strip()
        stored_code = request.session.get('email_code', '')
        expires = request.session.get('email_code_expires', 0)

        if time.time() > expires:
            del request.session['pending_reg']
            request.session.pop('email_code', None)
            request.session.pop('email_code_expires', None)
            request.session.pop('verify_attempts', None)
            return render(request, 'accounts/verify_email.html', {
                'email': pending['email'],
                'error': 'Код истёк. Зарегистрируйтесь заново.',
                'expired': True,
            })

        if entered == stored_code:
            del request.session['pending_reg']
            request.session.pop('email_code', None)
            request.session.pop('email_code_expires', None)
            request.session.pop('verify_attempts', None)

            if User.objects.filter(username=pending['username']).exists():
                return render(request, 'accounts/verify_email.html', {
                    'email': pending['email'],
                    'error': 'Это имя пользователя уже занято. Зарегистрируйтесь с другим именем.',
                    'expired': True,
                })

            try:
                user = User.objects.create_user(
                    username=pending['username'],
                    email=pending['email'],
                    password=pending['password'],
                )
                user.profile.phone = pending.get('phone', '')
                user.profile.save()
                login(request, user)
                return redirect('store:product_list')
            except IntegrityError:
                return render(request, 'accounts/verify_email.html', {
                    'email': pending['email'],
                    'error': 'Это имя пользователя уже занято. Зарегистрируйтесь с другим именем.',
                    'expired': True,
                })
        else:
            request.session['verify_attempts'] = attempts + 1
            error = 'Неверный код. Попробуйте ещё раз.'

    return render(request, 'accounts/verify_email.html', {
        'email': pending['email'],
        'error': error,
    })


@login_required
def profile(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    orders = request.user.orders.all()
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
