from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_image_size(image):
    if image.size > MAX_IMAGE_SIZE:
        raise ValidationError('Размер изображения не должен превышать 5 МБ.')


class Category(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, validators=[validate_image_size])

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:category', kwargs={'slug': self.slug})


class Product(models.Model):
    AVAILABILITY_IN_STOCK = 'in_stock'
    AVAILABILITY_OUT_OF_STOCK = 'out_of_stock'
    AVAILABILITY_COMING_SOON = 'coming_soon'
    AVAILABILITY_CHOICES = [
        (AVAILABILITY_IN_STOCK, 'В наличии'),
        (AVAILABILITY_OUT_OF_STOCK, 'Нет в наличии'),
        (AVAILABILITY_COMING_SOON, 'Скоро будет'),
    ]

    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='products/', blank=True, validators=[validate_image_size])
    size = models.CharField('Размер', max_length=100, blank=True)
    material = models.CharField('Материал', max_length=100, blank=True)
    pieces = models.PositiveIntegerField('Кол-во элементов', null=True, blank=True)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    availability_status = models.CharField(
        'Статус наличия',
        max_length=20,
        choices=AVAILABILITY_CHOICES,
        default=AVAILABILITY_IN_STOCK,
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Товар'
        verbose_name_plural = 'Товары'
        ordering = ['-created']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('store:product_detail', kwargs={'slug': self.slug})


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/gallery/', validators=[validate_image_size])
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Фото товара'
        verbose_name_plural = 'Фото товара'

    def __str__(self):
        return f'Фото #{self.order} — {self.product.name}'


class Favourite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favourites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favourited_by')
    quantity = models.PositiveIntegerField(default=1)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def get_total_price(self):
        return self.product.price * self.quantity

    def __str__(self):
        return f'{self.user.username} — {self.product.name}'
