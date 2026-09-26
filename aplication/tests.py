from io import BytesIO

from PIL import Image, ImageOps
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from .models import Product, ProductImage, UserProfile


class ProductMultiImageUploadTests(TestCase):
    def setUp(self):
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='strongpass123'
        )
        self.client.force_login(self.superuser)

    def test_upload_product_creates_multiple_images(self):
        image_1 = SimpleUploadedFile('first.jpg', b'fake-image-1', content_type='image/jpeg')
        image_2 = SimpleUploadedFile('second.jpg', b'fake-image-2', content_type='image/jpeg')

        response = self.client.post(
            '/upload-product/',
            {
                'name': 'Test Product',
                'description': 'A product with multiple photos',
                'price': '42.50',
                'original_price': '55.00',
                'tag': 'new',
                'images': [image_1, image_2],
            },
            follow=True,
            format='multipart',
        )

        self.assertEqual(response.status_code, 200)
        product = Product.objects.get(name='Test Product')
        self.assertEqual(product.images.count(), 2)
        self.assertTrue(product.images.filter(image__icontains='first').exists())
        self.assertTrue(product.images.filter(image__icontains='second').exists())
        self.assertIn(product, Product.objects.all())


class UserProfileImageOrientationTests(TestCase):
    def test_profile_picture_exif_orientation_is_normalized(self):
        user = User.objects.create_user(username='alice', password='secret123')

        image = Image.new('RGB', (200, 100), color='blue')
        exif = Image.Exif()
        exif[274] = 6

        buffer = BytesIO()
        image.save(buffer, format='JPEG', exif=exif.tobytes())
        buffer.seek(0)

        profile = UserProfile(user=user)
        profile.profile_picture.save('portrait.jpg', buffer, save=False)
        profile.save()

        with Image.open(profile.profile_picture) as rotated:
            self.assertEqual(rotated.size, (100, 200))
