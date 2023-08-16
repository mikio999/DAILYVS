# Generated by Django 4.2.3 on 2023-08-17 00:55

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('account', '0001_initial'),
        ('vote', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='voted_polls',
            field=models.ManyToManyField(blank=True, to='vote.poll'),
        ),
    ]
