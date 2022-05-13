
from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client

from django.urls import reverse

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
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем пользователя
    
        # Создаем второй клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    
    def test_url_everyone_uses_correct_template(self):
        """Проверка шаблонов для общедоступных адресов."""
        urls_status_code  = {
            'posts/index.html': reverse('posts:main'),
            'posts/group_list.html': reverse('posts:group', kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse('posts:profile', kwargs={'username': self.user.username}),
            'posts/post_detail.html': reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
            'posts/create_post.html': reverse('posts:post_create'),
            
        }
        for template, address in urls_status_code.items():
            with self.subTest(address=address):
                
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_authorized_uses_correct_template(self):
        """Проверка шаблонов для общедоступных адресов."""
        urls_status_code  = {
            'posts/create_post.html': reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),    
        }
        for template, address in urls_status_code.items():
            with self.subTest(address=address):
                
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_pages_is_only_author(self):
        """Страница /posts/<post_id>/edit/ доступна только автору."""
        response = self.authorized_author.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk})
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)


    def test_pages_is_available_to_everyone(self):
        """Проверка шаблонов для общедоступных адресов."""
        urls_status_code  = {
            reverse('posts:main'),
            reverse('posts:group', kwargs={'slug': self.group.slug}),
            reverse('posts:profile', kwargs={'username': self.user.username}),
            reverse('posts:post_detail', kwargs={'post_id': self.post.pk}),
        }
        for address in urls_status_code:
            with self.subTest(address=address):
                
                response = self.guest_client.get(address, follow=True)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )



    def test_pages_is_only_authorized(self):
        """Проверка шаблонов для общедоступных адресов."""
        urls_status_code  = {
            reverse('posts:post_create'),
            
        }
        for address in urls_status_code:
            with self.subTest(address=address):
                
                response = self.guest_client.get(address, follow=True)
                self.assertEqual(
                    response.status_code,
                    HTTPStatus.OK
                )


