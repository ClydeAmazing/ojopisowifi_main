# Generated by Django 2.1.7 on 2019-03-19 19:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0036_auto_20190320_0337'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='rates',
            options={'verbose_name': 'Rates', 'verbose_name_plural': 'Rates'},
        ),
        migrations.AddField(
            model_name='settings',
            name='Rate_Type',
            field=models.CharField(choices=[('auto', 'Minutes/Peso'), ('manual', 'Custom Rate')], default=1, max_length=25),
            preserve_default=False,
        ),
    ]
