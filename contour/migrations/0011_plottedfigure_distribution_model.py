# -*- coding: utf-8 -*-
# Generated by Django 1.11.11 on 2018-05-07 16:41
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contour', '0010_environmentalcontour_design_conditions_csv'),
    ]

    operations = [
        migrations.AddField(
            model_name='plottedfigure',
            name='distribution_model',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contour.DistributionModel'),
        ),
    ]
