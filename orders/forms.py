from django import forms


class CheckoutForm(forms.Form):
    full_name = forms.CharField(max_length=200, label='Полное имя')
    email = forms.EmailField(label='Email')
    phone = forms.CharField(max_length=20, label='Телефон')
    address = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), label='Адрес')
