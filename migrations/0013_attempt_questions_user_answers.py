# Generated by Django 5.1.1 on 2025-01-18 06:55

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobportalapp', '0012_subscriber'),
    ]

    operations = [
        migrations.CreateModel(
            name='Attempt',
            fields=[
                ('Attempt_id', models.AutoField(primary_key=True, serialize=False)),
                ('user_id', models.IntegerField()),
                ('Date', models.DateTimeField(auto_now_add=True)),
                ('obtained_marks', models.IntegerField(default=0)),
            ],
            options={
                'db_table': 'User_Attempts',
            },
        ),
        migrations.CreateModel(
            name='Questions',
            fields=[
                ('Question_num', models.AutoField(primary_key=True, serialize=False)),
                ('Question', models.CharField(max_length=200)),
                ('option_1', models.CharField(max_length=200)),
                ('option_2', models.CharField(max_length=200)),
                ('option_3', models.CharField(max_length=200)),
                ('option_4', models.CharField(max_length=200)),
                ('correct_answer', models.CharField(max_length=1)),
            ],
            options={
                'db_table': 'Aptitude_Questions',
            },
        ),
        migrations.CreateModel(
            name='User_answers',
            fields=[
                ('user_id', models.AutoField(primary_key=True, serialize=False)),
                ('answer', models.CharField(max_length=1)),
                ('mark', models.IntegerField()),
                ('Attempt_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jobportalapp.attempt')),
                ('question_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='jobportalapp.questions')),
            ],
            options={
                'db_table': 'Users_Answer',
            },
        ),
    ]
