import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('store', '0006_add_availability_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='discount',
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text='0 = без скидки. Введите значение от 0 до 100.',
                validators=[
                    django.core.validators.MinValueValidator(0),
                    django.core.validators.MaxValueValidator(100),
                ],
                verbose_name='Скидка (%)',
            ),
        ),
    ]
