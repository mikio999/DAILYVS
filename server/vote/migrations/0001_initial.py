# Generated by Django 4.2.3 on 2023-08-15 16:22

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Choice',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('choice_text', models.CharField(max_length=255)),
                ('image', models.ImageField(upload_to='')),
            ],
        ),
        migrations.CreateModel(
            name='Comment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('content', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='NonUserVote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('MBTI', models.TextField(null=True)),
                ('gender', models.CharField(choices=[('M', '남성'), ('W', '여성')], max_length=1, null=True, verbose_name='성별')),
            ],
        ),
        migrations.CreateModel(
            name='Poll',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.TextField()),
                ('content', models.TextField()),
                ('pub_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('active', models.BooleanField(default=True)),
                ('views_count', models.PositiveIntegerField(default=0)),
                ('thumbnail', models.ImageField(upload_to='')),
                ('comments', models.PositiveIntegerField(default=0, verbose_name='댓글수')),
            ],
        ),
        migrations.CreateModel(
            name='Poll_Result',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('total', models.PositiveIntegerField(default=0)),
                ('choice1_man', models.PositiveIntegerField(default=0)),
                ('choice2_man', models.PositiveIntegerField(default=0)),
                ('choice1_woman', models.PositiveIntegerField(default=0)),
                ('choice2_woman', models.PositiveIntegerField(default=0)),
                ('choice1_E', models.PositiveIntegerField(default=0)),
                ('choice2_E', models.PositiveIntegerField(default=0)),
                ('choice1_I', models.PositiveIntegerField(default=0)),
                ('choice2_I', models.PositiveIntegerField(default=0)),
                ('choice1_N', models.PositiveIntegerField(default=0)),
                ('choice2_N', models.PositiveIntegerField(default=0)),
                ('choice1_S', models.PositiveIntegerField(default=0)),
                ('choice2_S', models.PositiveIntegerField(default=0)),
                ('choice1_T', models.PositiveIntegerField(default=0)),
                ('choice2_T', models.PositiveIntegerField(default=0)),
                ('choice1_F', models.PositiveIntegerField(default=0)),
                ('choice2_F', models.PositiveIntegerField(default=0)),
                ('choice1_J', models.PositiveIntegerField(default=0)),
                ('choice2_J', models.PositiveIntegerField(default=0)),
                ('choice1_P', models.PositiveIntegerField(default=0)),
                ('choice2_P', models.PositiveIntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name='UserVote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('choice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vote.choice')),
                ('poll', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='vote.poll')),
            ],
        ),
    ]
