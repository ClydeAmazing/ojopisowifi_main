# Generated by Django 2.2.7 on 2019-11-27 05:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0059_auto_20191127_1222'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coinqueue',
            name='Total_Coins',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
