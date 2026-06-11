from django.contrib import admin
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
    list_display = ['name', 'category', 'price', 'stock', 'availability_status', 'available']
    list_filter = ['availability_status', 'available', 'category']
    list_editable = ['price', 'stock', 'availability_status', 'available']
    prepopulated_fields = {'slug': ('name',)}
    fieldsets = (
        (None, {
            'fields': ('category', 'name', 'slug', 'description', 'image', 'price')
        }),
        ('Наличие', {
            'fields': ('stock', 'availability_status', 'available'),
            'description': 'stock — внутренний остаток (виден только администратору). availability_status — что показывается покупателям вместо кнопки «Купить».',
        }),
        ('Характеристики', {
            'fields': ('size', 'material', 'pieces'),
            'description': 'Дополнительные характеристики товара (отображаются на странице товара)',
        }),
    )
