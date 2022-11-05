import shutil
import tempfile
from http import HTTPStatus

from django import forms
from django.conf import settings
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.shortcuts import get_object_or_404
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.forms import PostForm
from posts.models import Follow, Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем неавторизованный клиент
        cls.guest_client = Client()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='HasNoName')
        cls.user2 = User.objects.create_user(username='HasNoName2')

        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )

        cls.group = Group.objects.create(
            title='Тестовая Группа',
            slug='test-slug',
            description='тестовое описание группы'
        )

        cls.post = Post.objects.create(
            text='Тестовый текст',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )

    def setUp(self):
        # Создаем пользователя
        self.authorized_client = Client()
        # Создаем второй клиент
        self.authorized_client2 = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)
        # Авторизуем пользователя2
        self.authorized_client2.force_login(self.user2)
        # выборка всей ленты новостей
        author_querry = Follow.objects.filter(user=self.user)
        author_values_list = author_querry.values_list('author')
        self.post_list = Post.objects.filter(author_id__in=author_values_list)
        # добавление подписки
        self.follow = Follow.objects.create(
            user=self.user,
            author=self.post.author
        )
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_pages_posts_correct_template(self):
        """views функция использует соответствующий шаблон."""
        # Собираем в лист пары "имя_html_шаблона, reverse(name)"
        templates_pages_names = [
            (
                'posts/index.html',
                reverse('posts:index')
            ),
            (
                'posts/group_list.html', reverse(
                    'posts:group_list', kwargs={'slug': self.group.slug}
                )
            ),
            (
                'posts/profile.html', reverse(
                    'posts:profile',
                    args=[self.user]
                )
            ),
            (
                'posts/post_detail.html', reverse(
                    'posts:post_detail', kwargs={'post_id': self.post.pk}
                )
            ),
            (
                'posts/create_post.html', reverse(
                    'posts:create_post'
                )
            ),
            (
                'posts/create_post.html',
                reverse(
                    'posts:post_edit',
                    kwargs={'post_id': self.post.pk})
            )

        ]

        for template, reverse_name in templates_pages_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_pages_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""

        for post in Post.objects.select_related("group"):
            response = self.authorized_client.get(reverse('posts:index'))
            self.assertEqual(response.context.get('post'), post)

    def test_group_list_pages_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        )

        group = get_object_or_404(Group, slug=self.group.slug)
        first_objects = group.posts.all()
        for post in first_objects:
            self.assertEqual(response.context.get('post'), post)

        second_object = response.context.get('page_obj').object_list
        for post in second_object:
            self.assertEqual(response.context.get('post'), post)

    def test_profile_pages_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile',
            args=[self.user])
        )

        author = self.user
        first_objects = author.posts.all()
        for post in first_objects:
            self.assertEqual(response.context.get('post'), post)

        second_object = response.context.get('page_obj').object_list
        for post in second_object:
            self.assertEqual(response.context.get('post'), post)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(response.context.get('post'), self.post)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk}))
        )

        form_field = response.context.get('form').fields.get('text')
        self.assertIsInstance(form_field, forms.fields.CharField)

        form_field = response.context.get('form').fields.get('group')
        self.assertIsInstance(form_field, forms.fields.ChoiceField)

        form = response.context.get('form')
        self.assertIsInstance(form, PostForm)

    def test_create_post_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:create_post')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_show_correct_img_context(self):

        """Шаблоны сформированы с правильным контекстом

         проверка на наличие картинки"""
        url_names = [
            reverse('posts:index'),
            reverse('posts:group_list', args=['test-slug']),
            reverse('posts:profile', args=[self.user]),
            reverse('posts:post_detail', args=[self.post.pk]),
        ]

        for url in url_names:
            with self.subTest(value=url):
                response = self.authorized_client.get(url)
                self.assertEqual(
                    response.context.get('post').image,
                    self.post.image
                )

    def test_add_comment_correct_context(self):
        """Проверка add_comment

        комментарий появляется на странице поста
        комментировать посты может только авторизованный пользователь
        """
        url = reverse('posts:add_comment', args=[self.post.pk])
        response = self.authorized_client.get(url,)

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
                    'posts:add_comment', args=[self.post.pk])
            )

    def test_post_right_group_exists(self):
        """Проверка Создания Поста ,

        что если при создании поста указать группу то этот пост появляется."""

        response = self.authorized_client.get(
            reverse('posts:index')
        )
        object = self.group.posts.filter(
            group=response.context.get('post').group
        )
        self.assertTrue(object.exists())

        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        )

        object = self.group.posts.filter(
            group=response.context.get('post').group
        )
        self.assertTrue(object.exists())

    def test_post_right_group(self):
        response = self.authorized_client.get(
            reverse('posts:index')
        )

        for post in Post.objects.select_related("group"):
            self.assertEqual(response.context.get('post').group, post.group)

        response = self.authorized_client.get(reverse(
            'posts:group_list', kwargs={'slug': self.group.slug})
        )

        object = self.group.posts.all()
        for post in object:
            self.assertEqual(response.context.get('post').group, post.group)

    def test_follow(self):
        """Проверка авторизованный пользователь может

        подписываться на других пользователей """

        self.authorized_client.get(f'/profile/{self.user}/follow/')
        response = self.authorized_client.get('/follow/')

        for post in self.post_list:
            self.assertEqual(response.context.get('post'), post)

    def test_unfollow(self):
        """Проверка авторизованный пользователь может

        удалять других пользователей из подписок """

        self.authorized_client.get(f'/profile/{self.user}/unfollow/')
        response = self.authorized_client.get('/follow/')

        for post in self.post_list:
            self.assertEqual(response.context.get('post'), post)

    def test_check_correct_followed(self):
        """Проверка Ленты постов авторов

        Новая запись пользователя появляется в ленте
        тех, кто на него подписан"""

        response = self.authorized_client.get('/follow/')

        for post in self.post_list:
            self.assertEqual(response.context.get('post'), post)

    def test_check_correct_unfollowed(self):
        """Проверка Ленты постов авторов

        В ленте подписок нет лишних постов"""

        response = self.authorized_client2.get('/follow/')

        self.assertEqual(response.context.get('post'), None)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем пользователя
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

        cls.post = Post.objects.bulk_create(
            [
                Post(
                    text=f'Тестовый текст{i}',
                    author=cls.user,
                    group=cls.group
                )
                for i in range(0, 13)
            ]
        )

    def test_first_page_contains(self):
        """Тест Пагинатора для Первой странцы"""
        PAGE_LIMIT = 10
        url_names = {
            reverse('posts:index'): PAGE_LIMIT,
            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): PAGE_LIMIT,
            reverse(
                'posts:profile',
                args=[self.user]
            ): PAGE_LIMIT,
        }

        for value, expected in url_names.items():
            with self.subTest(value=value):
                response = self.client.get(value + '?page=1')
                self.assertEqual(len(response.context['page_obj']), expected)

    def test_second_page_contains_three_records(self):
        """Тест Пагинатора для Второй странцы"""
        PAGE_LIMIT_SECOND_PAGE = 3

        url_names = {
            reverse(
                'posts:index'
            ): PAGE_LIMIT_SECOND_PAGE,

            reverse(
                'posts:group_list',
                kwargs={'slug': self.group.slug}
            ): PAGE_LIMIT_SECOND_PAGE,

            reverse(
                'posts:profile',
                args=[self.user]
            ): PAGE_LIMIT_SECOND_PAGE,
        }

        for value, expected in url_names.items():
            with self.subTest(value=value):
                response = self.client.get(value + '?page=2')
                self.assertEqual(len(response.context['page_obj']), expected)
