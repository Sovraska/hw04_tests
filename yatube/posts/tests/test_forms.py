import shutil
import tempfile

from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Group, Post, User

# Создаем временную папку для медиа-файлов;
# на момент теста медиа папка будет переопределена
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


# Для сохранения media-файлов в тестах будет использоваться
# временная папка TEMP_MEDIA_ROOT, а потом мы ее удалим
@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):

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
        # Создаем форму, если нужна проверка атрибутов
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Валидная форма create_post создает запись в Post."""

        tasks_count = Post.objects.count()

        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:create_post'),
            data={'text': 'Тестовый текст'},
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse(
            'posts:profile', args=['HasNoName'])
        )

        # Проверяем, увеличилось ли число постов
        self.assertEqual(Post.objects.count(), tasks_count + 1)

    def test_post_edit(self):
        """Валидная форма post_edit создает запись в Post."""

        # Отправляем POST-запрос
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[1]),
            data={'text': 'Тестовый текст2'},
        )
        # Проверяем, сработал ли редирект
        self.assertRedirects(response, reverse('posts:post_detail', args=[1]))

        self.assertTrue(Post.objects.filter(text='Тестовый текст2',).exists())
