from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from ..models import Group, Post

User = get_user_model()


class PostUrlTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='testnoname')
        cls.author = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_url_everyone_uses_correct_template(self):
        """Проверка шаблонов для адресов."""
        urls_status_code = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.group.slug}/',
            'posts/profile.html': f'/profile/{self.user.username}/',
            'posts/post_detail.html': f'/posts/{self.post.pk}/',
        }
        urls_status_code_author = {
            'posts/create_post.html': f'/posts/{self.post.pk}/edit/',
        }
        urls_status_code_authorized = {
            'posts/create_post.html': '/create/',
        }

        for template, address in urls_status_code.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)

        for template, address in urls_status_code_author.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

        for template, address in urls_status_code_authorized.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_pages_is_only_author(self):
        """Страница /posts/<post_id>/edit/ доступна только автору."""
        response = self.authorized_author.get(
            f'/posts/{self.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_pages_is_available_to_everyone(self):
        """Проверка общедоступных адресов."""
        urls_status_code = {
            '/',
            f'/group/{self.group.slug}/',
            f'/profile/{self.user.username}/',
            f'/posts/{self.post.pk}/',
        }
        for address in urls_status_code:
            with self.subTest(address=address):
                response = self.client.get(address, follow=True)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )

    def test_pages_is_only_authorized(self):
        """Проверка адресов только для авторизованных."""
        urls_status_code = {
            '/create/',
            f'/posts/{self.post.pk}/comment/',
        }
        for address in urls_status_code:
            with self.subTest(address=address):
                response = self.authorized_client.get(address, follow=True)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )

    def test_pages_is_not_found(self):
        """Проверка адресов для несуществующих страниц."""
        response = self.client.get('/dawdawdwa')
        self.assertEqual(response.status_code, 404)
