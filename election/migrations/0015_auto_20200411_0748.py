# Generated by Django 3.0.1 on 2020-04-11 07:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('election', '0014_auto_20200323_1012'),
    ]

    operations = [
        migrations.AlterField(
            model_name='election',
            name='finished_at',
            field=models.IntegerField(default=1586591289, verbose_name='End date'),
        ),
        migrations.AlterField(
            model_name='election',
            name='started_at',
            field=models.IntegerField(default=1586591288, verbose_name='Start date'),
        ),
    ]
