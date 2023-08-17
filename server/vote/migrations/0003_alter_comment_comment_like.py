# Generated by Django 4.2.4 on 2023-08-17 16:42

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("vote", "0002_comment_comment_like"),
    ]

    operations = [
        migrations.AlterField(
            model_name="comment",
            name="comment_like",
            field=models.ManyToManyField(
                blank=True, related_name="comment_like", to=settings.AUTH_USER_MODEL
            ),
        ),
    ]
