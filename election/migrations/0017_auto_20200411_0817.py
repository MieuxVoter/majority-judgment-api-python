# Generated by Django 3.0.1 on 2020-04-11 08:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('election', '0016_auto_20200411_0817'),
    ]

    operations = [
        migrations.AlterField(
            model_name='election',
            name='finish_at',
            field=models.IntegerField(default=1586593052, verbose_name='End date'),
        ),
        migrations.AlterField(
            model_name='election',
            name='start_at',
            field=models.IntegerField(default=1586593051, verbose_name='Start date'),
        ),
    ]