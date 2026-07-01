from decimal import Decimal

from django.contrib import admin, messages
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.html import format_html

from .models import Category, Product, ProductImage


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3
    fields = ['image', 'order']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline]
    change_list_template = 'admin/store/product/change_list.html'

    list_display = [
        'name', 'category', 'price', 'discount',
        'discounted_price_display', 'stock', 'availability_status', 'available',
    ]
    list_filter = ['availability_status', 'available', 'category']
    list_editable = ['price', 'discount', 'stock', 'availability_status', 'available']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['discounted_price_display']
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug', 'description', 'image'),
        }),
        ('Цена и скидка', {
            'fields': ('price', 'discount', 'discounted_price_display'),
            'description': (
                'Установите скидку в процентах (0–100). '
                'Цена со скидкой рассчитывается автоматически.'
            ),
        }),
        ('Наличие', {
            'fields': ('stock', 'availability_status', 'available'),
            'description': (
                'stock — внутренний остаток (виден только администратору). '
                'availability_status — что показывается покупателям вместо кнопки «Купить».'
            ),
        }),
        ('Характеристики', {
            'fields': ('size', 'material', 'pieces'),
            'description': 'Дополнительные характеристики товара (отображаются на странице товара)',
        }),
    )

    # ------------------------------------------------------------------ #
    # Custom URL: /admin/store/product/global-discount/                   #
    # ------------------------------------------------------------------ #
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                'global-discount/',
                self.admin_site.admin_view(self.global_discount_view),
                name='store_product_global_discount',
            ),
        ]
        return custom + urls

    def global_discount_view(self, request):
        if request.method == 'POST':
            action = request.POST.get('action')

            if action == 'apply':
                raw = request.POST.get('discount', '').strip()
                try:
                    pct = int(raw)
                    if not 0 <= pct <= 100:
                        raise ValueError
                except (ValueError, TypeError):
                    messages.error(
                        request,
                        'Некорректное значение. Введите целое число от 0 до 100.',
                    )
                    return redirect('.')

                count = Product.objects.count()
                Product.objects.update(discount=pct)
                if pct == 0:
                    messages.success(
                        request,
                        f'Скидка снята со всех {count} товаров.',
                    )
                else:
                    messages.success(
                        request,
                        f'Скидка {pct}% применена к {count} товарам.',
                    )
                return redirect('.')

            if action == 'remove':
                count = Product.objects.filter(discount__gt=0).count()
                Product.objects.update(discount=0)
                messages.success(
                    request,
                    f'Скидка снята с {count} товаров.',
                )
                return redirect('.')

        total = Product.objects.count()
        with_discount = Product.objects.filter(discount__gt=0).count()
        no_discount = total - with_discount

        # Current global discount (only meaningful if all products share it)
        discounts = (
            Product.objects.filter(discount__gt=0)
            .values_list('discount', flat=True)
            .distinct()
        )
        current_discount = discounts[0] if discounts.count() == 1 else None

        context = {
            **self.admin_site.each_context(request),
            'title': 'Глобальная скидка',
            'opts': self.model._meta,
            'total': total,
            'with_discount': with_discount,
            'no_discount': no_discount,
            'current_discount': current_discount,
        }
        return render(request, 'admin/store/product/global_discount.html', context)

    # ------------------------------------------------------------------ #
    # Helper column                                                        #
    # ------------------------------------------------------------------ #
    @admin.display(description='Цена со скидкой')
    def discounted_price_display(self, obj):
        if obj.discount:
            return format_html(
                '<span style="color:#16a34a;font-weight:700;">{}</span> '
                '<span style="color:#888;font-size:11px;">(-{}%)</span>',
                obj.discounted_price,
                obj.discount,
            )
        return format_html('<span style="color:#888;">—</span>')
