# Generated by Django 3.0.8 on 2020-11-30 06:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0103_auto_20201130_1440'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coinslot',
            name='Last_Updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
