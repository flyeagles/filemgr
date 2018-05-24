# Generated by Django 2.0.1 on 2018-01-16 10:49

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('fileondisk', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Disk',
            fields=[
                ('serial_no', models.TextField(primary_key=True, serialize=False)),
                ('disk_model', models.TextField()),
                ('disk_index', models.IntegerField()),
                ('size', models.IntegerField()),
                ('partitions', models.IntegerField()),
                ('SMART_pass', models.IntegerField()),
                ('SMART_info', models.TextField()),
                ('machine', models.TextField()),
                ('media_type', models.TextField()),
            ],
        ),
        migrations.CreateModel(
            name='FileInfo',
            fields=[
                ('fname', models.TextField()),
                ('size', models.IntegerField()),
                ('file_type', models.TextField()),
                ('mod_time', models.IntegerField()),
                ('folder', models.TextField()),
                ('fullname', models.TextField()),
                ('fullvolpath', models.TextField(primary_key=True, serialize=False)),
            ],
        ),
        migrations.CreateModel(
            name='Volume',
            fields=[
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('volume_name', models.TextField()),
                ('size', models.IntegerField()),
                ('size_free', models.IntegerField()),
                ('disk', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='fileondisk.Disk')),
            ],
        ),
        migrations.AddField(
            model_name='fileinfo',
            name='volume',
            field=models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='fileondisk.Volume'),
        ),
    ]