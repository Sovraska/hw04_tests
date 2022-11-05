from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class CoreViewsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Создаем неавторизованный клиент
        cls.guest_client = Client()
        # Создаем пользователя
        cls.user = User.objects.create_user(username='HasNoName')

    def test_urls_uses_correct_template(self):
        """add_coment использует соответствующий шаблон."""

        response = self.guest_client.get('/unexisting_page/')
        self.assertTemplateUsed(response, 'core/404.html')
