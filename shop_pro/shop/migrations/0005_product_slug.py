# Generated by Django 5.1.3 on 2024-11-20 13:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_checkout_order_status_alter_checkout_payment_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='product',
            name='slug',
            field=models.SlugField(blank=True, unique=True),
        ),
    ]