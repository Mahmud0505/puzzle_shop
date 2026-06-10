import re
from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


def clean_tj_phone(value):
    """Принимает 9 цифр (без кода), возвращает +992XXXXXXXXX."""
    digits = re.sub(r'\D', '', value)
    # Если пользователь вставил полный номер с кодом 992
    if digits.startswith('992') and len(digits) == 12:
        digits = digits[3:]
    if len(digits) != 9:
        raise forms.ValidationError('Введите ровно 9 цифр номера (без кода страны).')
    return '+992' + digits


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    phone = forms.CharField(max_length=20, required=False, label='Номер телефона')

    class Meta:
        model = User
        fields = ('username', 'email', 'phone', 'password1', 'password2')

    def clean_phone(self):
        value = self.cleaned_data.get('phone', '').strip()
        if not value:
            return ''
        return clean_tj_phone(value)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            user.profile.phone = self.cleaned_data.get('phone', '')
            user.profile.save()
        return user


class AddressForm(forms.ModelForm):
    phone = forms.CharField(max_length=20, required=False, label='Номер телефона')

    class Meta:
        model = UserProfile
        fields = ('phone', 'city', 'address', 'courier_comment')
        labels = {
            'city': 'Город',
            'address': 'Адрес доставки',
            'courier_comment': 'Комментарий для курьера',
        }
        widgets = {
            'city': forms.TextInput(attrs={'placeholder': 'Душанбе'}),
            'address': forms.TextInput(attrs={'placeholder': 'ул. Рудаки 10, кв. 5'}),
            'courier_comment': forms.TextInput(attrs={'placeholder': 'Код домофона, этаж, ориентир...'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Показываем только 9 цифр без +992 в поле
        instance = kwargs.get('instance')
        if instance and instance.phone and instance.phone.startswith('+992'):
            self.fields['phone'].initial = instance.phone[4:]

    def clean_phone(self):
        value = self.cleaned_data.get('phone', '').strip()
        if not value:
            return ''
        return clean_tj_phone(value)
