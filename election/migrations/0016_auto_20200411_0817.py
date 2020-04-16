# Generated by Django 3.0.1 on 2020-04-11 08:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('election', '0015_auto_20200411_0748'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='election',
            name='finished_at',
        ),
        migrations.RemoveField(
            model_name='election',
            name='started_at',
        ),
        migrations.AddField(
            model_name='election',
            name='finish_at',
            field=models.IntegerField(default=1586593030, verbose_name='End date'),
        ),
        migrations.AddField(
            model_name='election',
            name='start_at',
            field=models.IntegerField(default=1586593029, verbose_name='Start date'),
        ),
    ]
