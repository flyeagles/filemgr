# Generated by Django 2.0.1 on 2018-01-18 13:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('fileondisk', '0002_auto_20180116_1849'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='fileinfo',
            name='fullvolpath',
        ),
        migrations.AddField(
            model_name='fileinfo',
            name='id',
            field=models.AutoField(auto_created=True, default=1, primary_key=True, serialize=False, verbose_name='ID'),
            preserve_default=False,
        ),
    ]
