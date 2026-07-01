from django.contrib import admin
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
