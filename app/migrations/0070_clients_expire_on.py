# Generated by Django 2.2.7 on 2020-01-10 12:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0069_auto_20200109_0130'),
    ]

    operations = [
        migrations.AddField(
            model_name='clients',
            name='Expire_On',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
