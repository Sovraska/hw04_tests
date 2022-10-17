from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import User


class StaticViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем неавторизованный клиент
        cls.guest_client = Client()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='HasNoName')
        # Создаем второй клиент
        cls.authorized_client = Client()
        # Авторизуем пользователя
        cls.authorized_client.force_login(cls.user)

    def test_pages_accessible_by_name(self):
        '''проверка HTTPStatus.OK для author,tech'''
        staic_pages = {
            'about:author': HTTPStatus.OK,
            'about:tech': HTTPStatus.OK,
        }

        for page, status_code in staic_pages.items():
            with self.subTest(page=page):
                response = self.guest_client.get(reverse(page))
                self.assertEqual(response.status_code, status_code)

    def test_pages_uses_correct_template(self):
        """применяется нужный шаблон к URL's"""
        staic_templates_pages_names = {
            'about/author.html': reverse('about:author'),
            'about/tech.html': reverse('about:tech'),
        }

        for template, reverse_name in staic_templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
