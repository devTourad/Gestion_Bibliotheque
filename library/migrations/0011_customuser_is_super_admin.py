# Generated by Django 5.1.4 on 2025-06-12 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0010_delivery'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='is_super_admin',
            field=models.BooleanField(default=False, verbose_name='Super administrateur'),
        ),
    ]
