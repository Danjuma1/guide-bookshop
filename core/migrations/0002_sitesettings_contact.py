from django.db import migrations, models


def seed_contact(apps, schema_editor):
    SiteSettings = apps.get_model('core', 'SiteSettings')
    obj, _ = SiteSettings.objects.get_or_create(pk=1)
    obj.address = '9, Alaja Road, Megida Bus Stop, Ayobo, Lagos 300001'
    obj.phone = '08028872962'
    obj.google_maps_url = 'https://share.google/emRjct0VspL1Mybg5'
    obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='google_maps_url',
            field=models.URLField(blank=True),
        ),
        migrations.RunPython(seed_contact, migrations.RunPython.noop),
    ]
