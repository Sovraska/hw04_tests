from http import HTTPStatus

from django import forms
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post

User = get_user_model()


class UsersTests(TestCase):
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

        group = Group.objects.create(
            title='Тестовая Группа',
            slug='test-slug',
            description='тестовое описание группы'
        )
        Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=group,
        )

    def test_task_detail_url_exists_at_desired_location(self):
        """проверка доступности страниц любому пользователю."""
        url_names = [
            '/auth/signup/',
            '/auth/logout/',
            '/auth/login/',
            '/auth/password_reset/',
            '/auth/reset/done/',
        ]

        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_home_url_exists_for_author(self):
        """проверка доступности страниц только автору."""
        url_names = [
            '/auth/password_change/done/',
            '/auth/password_change/',
            '/auth/password_reset/done/',
        ]

        for url in url_names:
            with self.subTest(url=url):
                post_user = get_object_or_404(User, username='HasNoName')
                if post_user == self.authorized_client:
                    response = self.authorized_client.get(url)
                    self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон

         для авториозванного пользователя."""
        # Шаблоны по адресам
        templates_url_names = {
            'users/signup.html': reverse('users:signup'),
            'users/logged_out.html': reverse('users:logout'),
            'users/login.html': reverse('users:login'),
            'users/password_reset_form.html': reverse('users:password_reset'),
            'users/password_reset_done.html': reverse(
                'users:password_reset_done'
            ),


        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_for_author(self):
        """URL-адрес использует соответствующий шаблон

        для авториозванного пользователя-автора."""
        # Шаблоны по адресам
        templates_url_names = {
            'users/password_change.html': reverse(
                'users:password_change_done'
            ),
            'users/password_reset_done.html': reverse(
                'users:password_reset_done'
            ),
            'users:password_change_done': reverse(
                'users:password_change'
            ),
        }
        for template, address in templates_url_names.items():
            with self.subTest(address=address):
                post_user = get_object_or_404(User, username='HasNoName')
                if post_user == self.authorized_client:
                    response = self.authorized_client.get(address)
                    self.assertTemplateUsed(response, template)

    def test_signup_show_correct_context(self):
        """Шаблон signup сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('users:signup'))

        form_fields = {
            'first_name': forms.fields.CharField,
            'last_name': forms.fields.CharField,
            'username': forms.fields.CharField,
            'email': forms.fields.EmailField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)
