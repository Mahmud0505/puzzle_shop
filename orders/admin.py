from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['product', 'price', 'quantity', 'get_total_price']
    fields = ['product', 'price', 'quantity', 'get_total_price']

    def get_total_price(self, obj):
        return f'{obj.get_total_price()} сом'
    get_total_price.short_description = 'Сумма'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'full_name', 'user', 'status_badge',
        'total_price', 'created', 'updated',
    ]
    list_filter = ['status', 'created']
    search_fields = ['full_name', 'email', 'phone', 'user__username']
    readonly_fields = ['user', 'full_name', 'email', 'phone', 'address', 'total_price', 'created', 'updated']
    ordering = ['-created']
    inlines = [OrderItemInline]
    actions = ['mark_processing', 'mark_shipped', 'mark_delivered', 'mark_cancelled']

    fieldsets = (
        ('Статус заказа', {
            'fields': ('status',),
        }),
        ('Покупатель', {
            'fields': ('user', 'full_name', 'email', 'phone'),
        }),
        ('Доставка', {
            'fields': ('address',),
        }),
        ('Итог', {
            'fields': ('total_price', 'created', 'updated'),
        }),
    )

    def status_badge(self, obj):
        colors = {
            'pending':    ('#b45309', '#fef3c7'),
            'processing': ('#1d4ed8', '#dbeafe'),
            'shipped':    ('#6d28d9', '#ede9fe'),
            'delivered':  ('#15803d', '#dcfce7'),
            'cancelled':  ('#b91c1c', '#fee2e2'),
        }
        fg, bg = colors.get(obj.status, ('#333', '#eee'))
        return format_html(
            '<span style="'
            'display:inline-block;padding:3px 10px;border-radius:20px;'
            'font-size:12px;font-weight:600;'
            'color:{};background:{};">{}</span>',
            fg, bg, obj.get_status_display()
        )
    status_badge.short_description = 'Статус'

    @admin.action(description='Пометить как «В обработке»')
    def mark_processing(self, request, queryset):
        updated = queryset.exclude(status='cancelled').update(status='processing')
        self.message_user(request, f'{updated} заказ(ов) переведено в «В обработке».')

    @admin.action(description='Пометить как «В пути»')
    def mark_shipped(self, request, queryset):
        updated = queryset.exclude(status='cancelled').update(status='shipped')
        self.message_user(request, f'{updated} заказ(ов) переведено в «В пути».')

    @admin.action(description='Пометить как «Доставлено»')
    def mark_delivered(self, request, queryset):
        updated = queryset.exclude(status='cancelled').update(status='delivered')
        self.message_user(request, f'{updated} заказ(ов) переведено в «Доставлено».')

    @admin.action(description='Пометить как «Отменено»')
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, f'{updated} заказ(ов) отменено.')
