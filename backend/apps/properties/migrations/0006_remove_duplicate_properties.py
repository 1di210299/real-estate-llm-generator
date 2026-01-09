# Generated manually on 2026-01-09 21:05
# Data migration to remove duplicate properties before adding unique constraint

from django.db import migrations


def remove_duplicate_properties(apps, schema_editor):
    """Remove duplicate properties keeping the most recent one."""
    Property = apps.get_model('properties', 'Property')
    
    # Find all properties with source_url
    all_properties = Property.objects.filter(source_url__isnull=False).order_by('tenant_id', 'source_url', '-created_at')
    
    seen = set()
    duplicates_to_delete = []
    
    for prop in all_properties:
        key = (str(prop.tenant_id), prop.source_url)
        if key in seen:
            # This is a duplicate, mark for deletion
            duplicates_to_delete.append(prop.id)
        else:
            # First occurrence, keep it
            seen.add(key)
    
    if duplicates_to_delete:
        deleted_count = Property.objects.filter(id__in=duplicates_to_delete).delete()[0]
        print(f"Removed {deleted_count} duplicate properties")
    else:
        print("No duplicate properties found")


def reverse_migration(apps, schema_editor):
    """No reverse operation needed."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('properties', '0005_alter_propertyimage_image_url'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_properties, reverse_migration),
    ]
