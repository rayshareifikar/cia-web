# Generated by Django 5.1.2 on 2024-10-26 06:42

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('places', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='comment',
            options={'ordering': ['-created_at']},
        ),
        migrations.RemoveField(
            model_name='place',
            name='location',
        ),
        migrations.RemoveField(
            model_name='place',
            name='rating_avg',
        ),
        migrations.AddField(
            model_name='comment',
            name='rating',
            field=models.PositiveIntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')], default=3),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='comments', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='place',
            name='image',
            field=models.ImageField(upload_to='places/images/'),
        ),
        migrations.AlterField(
            model_name='souvenir',
            name='image',
            field=models.ImageField(upload_to='souvenirs/images/'),
        ),
        migrations.AlterField(
            model_name='souvenir',
            name='stock',
            field=models.PositiveIntegerField(),
        ),
        migrations.DeleteModel(
            name='Rating',
        ),
    ]
