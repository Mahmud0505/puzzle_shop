import urllib.request
import urllib.parse
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


def _send(text):
    token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID
    if not token or not chat_id:
        return
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    data = urllib.parse.urlencode({
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML',
    }).encode()
    try:
        req = urllib.request.Request(url, data=data, method='POST')
        urllib.request.urlopen(req, timeout=5)
    except Exception as e:
        logger.warning('Telegram notification failed: %s', e)


def _fmt(value):
    return f'{value:,.2f}'.replace(',', ' ').replace('.', ',') + 'с'


def send_order_notification(order):
    items = order.items.select_related('product').all()
    items_text = '\n'.join(
        f'  • {item.product.name} × {item.quantity} = {_fmt(item.price * item.quantity)}'
        for item in items
    )
    subtotal = sum(item.price * item.quantity for item in items)
    delivery = order.total_price - subtotal
    if delivery <= 0:
        delivery_line = '🚚 Доставка: Бесплатно'
    else:
        delivery_line = f'🚚 Доставка: {_fmt(delivery)}'

    text = (
        f'🛒 Новый заказ #{order.pk}\n'
        f'\n'
        f'👤 Покупатель: {order.full_name}\n'
        f'📞 Телефон: {order.phone or "—"}\n'
        f'📍 Адрес: {order.address or "—"}\n'
        f'\n'
        f'📦 Товары:\n{items_text}\n'
        f'\n'
        f'{delivery_line}\n'
        f'💰 Итого: {_fmt(order.total_price)}'
    )
    _send(text)


def send_cancel_notification(order):
    items = order.items.select_related('product').all()
    items_text = '\n'.join(
        f'  • {item.product.name} × {item.quantity}'
        for item in items
    )
    text = (
        f'❌ Заказ #{order.pk} отменён\n'
        f'\n'
        f'👤 Покупатель: {order.full_name}\n'
        f'📞 Телефон: {order.phone or "—"}\n'
        f'\n'
        f'📦 Товары:\n{items_text}\n'
        f'\n'
        f'💰 Сумма заказа: {_fmt(order.total_price)}'
    )
    _send(text)
