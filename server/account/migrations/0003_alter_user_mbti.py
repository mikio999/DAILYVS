# Generated by Django 4.2.3 on 2023-08-08 15:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0002_nonuser'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='mbti',
            field=models.CharField(choices=[('INFP', 'INFP'), ('ENFP', 'ENFP'), ('INFJ', 'INFJ'), ('ENFJ', 'ENFJ'), ('INTJ', 'INTJ'), ('ENTJ', 'ENTJ'), ('INTP', 'INTP'), ('ENTP', 'ENTP'), ('ISFP', 'ISFP'), ('ESFP', 'ESFP'), ('ISFJ', 'ISFJ'), ('ESFJ', 'ESFJ'), ('ISTP', 'ISTP'), ('ESTP', 'ESTP'), ('ISTJ', 'ISTJ'), ('ESTJ', 'ESTJ')], max_length=4, verbose_name='MBTI'),
        ),
    ]
