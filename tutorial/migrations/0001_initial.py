# Generated by Django 3.2 on 2021-09-14 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='No Title', max_length=264)),
                ('email', models.CharField(default='No Title', max_length=264)),
            ],
        ),
    ]
