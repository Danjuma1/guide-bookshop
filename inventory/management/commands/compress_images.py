"""
Management command to compress all existing product images.

Usage:
    python manage.py compress_images
    python manage.py compress_images --quality 80   (default: 75)
    python manage.py compress_images --max-size 600  (default: 800px)
    python manage.py compress_images --dry-run       (preview savings without changing files)
"""

import io
import os
from django.core.management.base import BaseCommand
from PIL import Image


class Command(BaseCommand):
    help = 'Compress and resize all existing product images in-place'

    def add_arguments(self, parser):
        parser.add_argument(
            '--quality', type=int, default=75,
            help='JPEG quality (1-95). Default: 75'
        )
        parser.add_argument(
            '--max-size', type=int, default=800,
            help='Max width or height in pixels. Default: 800'
        )
        parser.add_argument(
            '--dry-run', action='store_true',
            help='Show what would happen without changing any files'
        )

    def handle(self, *args, **options):
        from inventory.models import Product

        quality = options['quality']
        max_dim = options['max_size']
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN — no files will be changed\n'))

        products = Product.objects.exclude(image='').exclude(image=None)
        total = products.count()

        if total == 0:
            self.stdout.write('No product images found.')
            return

        self.stdout.write(f'Found {total} product(s) with images.\n')

        total_before = 0
        total_after = 0
        compressed = 0
        skipped = 0
        errors = 0

        for product in products:
            try:
                path = product.image.path
                if not os.path.exists(path):
                    self.stdout.write(self.style.WARNING(f'  [MISSING] {product.name}: file not found, skipping'))
                    skipped += 1
                    continue

                original_size = os.path.getsize(path)
                total_before += original_size

                img = Image.open(path)

                # Convert to RGB (handles PNG with transparency, palette images, etc.)
                if img.mode in ('RGBA', 'P', 'LA', 'L'):
                    img = img.convert('RGB')

                # Resize if needed
                needs_resize = img.width > max_dim or img.height > max_dim
                if needs_resize:
                    img.thumbnail((max_dim, max_dim), Image.LANCZOS)

                # Write compressed version to memory to measure size first
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=quality, optimize=True)
                new_size = buf.tell()
                total_after += new_size

                savings_pct = (1 - new_size / original_size) * 100 if original_size > 0 else 0
                dim_info = f' | resized to {img.width}×{img.height}' if needs_resize else ''

                self.stdout.write(
                    f'  {product.name[:45]:<45} '
                    f'{original_size // 1024:>5}KB -> {new_size // 1024:>4}KB  '
                    f'({savings_pct:+.0f}%){dim_info}'
                )

                if not dry_run:
                    # Write compressed bytes back to disk (replace original)
                    buf.seek(0)
                    with open(path, 'wb') as f:
                        f.write(buf.read())

                    # Rename to .jpg if extension differs
                    ext = os.path.splitext(path)[1].lower()
                    if ext not in ('.jpg', '.jpeg'):
                        new_path = os.path.splitext(path)[0] + '.jpg'
                        os.rename(path, new_path)
                        # Update the DB field to point to the new filename
                        new_name = os.path.splitext(product.image.name)[0] + '.jpg'
                        Product.objects.filter(pk=product.pk).update(image=new_name)

                compressed += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  [ERROR] {product.name}: {e}'))
                errors += 1

        # Summary
        self.stdout.write('')
        saved_kb = (total_before - total_after) // 1024
        saved_pct = (1 - total_after / total_before) * 100 if total_before > 0 else 0
        action = 'Would save' if dry_run else 'Saved'

        self.stdout.write(self.style.SUCCESS(
            f'Done: {compressed} compressed, {skipped} skipped, {errors} errors\n'
            f'{action} {saved_kb:,} KB ({saved_pct:.0f}% reduction) '
            f'— {total_before // 1024:,} KB -> {total_after // 1024:,} KB'
        ))
