from django.db import migrations, models


def update_role_values(apps, schema_editor):
    StaffProfile = apps.get_model('accounts', 'StaffProfile')
    mapping = {
        'manager':   'store_manager',
        'inventory': 'inventory_clerk',
        'sales':     'sales_associate',
    }
    for old, new in mapping.items():
        StaffProfile.objects.filter(role=old).update(role=new)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0002_staffprofile_module_permissions'),
    ]
    operations = [
        migrations.AlterField(
            model_name='staffprofile',
            name='role',
            field=models.CharField(
                max_length=20,
                choices=[
                    ('super_admin', 'Super Admin'),
                    ('admin', 'Admin'),
                    ('store_manager', 'Store Manager'),
                    ('sales_associate', 'Sales Associate'),
                    ('inventory_clerk', 'Inventory Clerk'),
                    ('cashier', 'Cashier'),
                ],
                default='cashier',
            ),
        ),
        migrations.RunPython(update_role_values, migrations.RunPython.noop),
    ]
