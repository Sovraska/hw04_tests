from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse

from posts.models import Group, Post, User


class PostURLTests(TestCase):
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

        cls.group = Group.objects.create(
            title='Тестовая Группа',
            slug='test-slug',
            description='тестовое описание группы'
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
        )

    def test_url_exists_at_desired_location(self):
        """проверка доступности страниц любому пользователю."""
        url_names = [
            reverse('posts:index'),
            reverse('posts:group_list', args=['test-slug']),
            reverse('posts:profile', args=[self.user]),
            reverse('posts:post_detail', args=[self.post.pk]),
        ]

        for url in url_names:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)

    def test_url_exists_at_desired_location_authorized(self):
        """проверка доступности страниц авторизованному пользователю тоже."""
        url_names = [
            reverse('posts:index'),
            reverse('posts:group_list', args=['test-slug']),
            reverse('posts:profile', args=[self.user]),
            reverse('posts:post_detail', args=[self.post.pk]),
            reverse('posts:create_post'),

        ]
        for url in url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_home_url_exists_for_author(self):
        """проверка доступности страниц только автору."""
        url_names = [
            reverse('posts:post_edit', args=[self.post.pk]),
        ]

        for url in url_names:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)

                if self.post.author == self.authorized_client:
                    self.assertEqual(response.status_code, HTTPStatus.OK)

                elif self.user == self.authorized_client:
                    self.assertRedirects(response, url)

                else:
                    response = self.guest_client.get(url)
                    self.assertRedirects(
                        response, reverse(
                            'users:login'
                        ) + "?next=" + reverse(
                            'posts:post_edit', args=[self.post.pk])
                    )

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        # Шаблоны по адресам
        templates_url_names = {
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:group_list', args=['test-slug']):
            'posts/group_list.html',
            reverse('posts:profile', args=[self.user]):
            'posts/profile.html',
            reverse('posts:post_detail', args=[self.post.pk]):
            'posts/post_detail.html',
            reverse('posts:post_edit', args=[self.post.pk]):
            'posts/create_post.html',
            reverse('posts:create_post'): 'posts/create_post.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
