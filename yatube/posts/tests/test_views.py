
from django import forms
from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostViewTest(TestCase):
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

        cls.group_second = Group.objects.create(
            title='Тестовая группа 2',
            slug='test-slug-two',
            description='Тестовое описание 2',
        )

        cls.post_test = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group_second
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group
        )
        for index in range(12):
            cls.index = Post.objects.create(
                author=cls.author,
                text='Тестовый пост',
                group=cls.group
            )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_url_everyone_uses_correct_template(self):
        """Проверка шаблонов для общедоступных адресов."""

        urls_status_code = {
            'posts/index.html': reverse('posts:main'),
            'posts/group_list.html': reverse(
                'posts:group', kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse(
                'posts:profile', kwargs={'username': self.user.username}),
            'posts/post_detail.html': reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}),
            'posts/create_post.html': reverse('posts:post_create'),
        }
        for template, address in urls_status_code.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_url_authorized_uses_correct_template(self):
        """Проверка шаблонов для общедоступных адресов."""
        urls_status_code = {
            'posts/create_post.html': reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}),
        }
        for template, address in urls_status_code.items():
            with self.subTest(address=address):

                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_task_list_page_show_correct_context(self):
        """Шаблон task_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:main'))
        # Взяли первый элемент из списка и проверили, что его содержание
        # совпадает с ожидаемым
        first_object = response.context['page_obj'][0]
        task_text_0 = first_object.text
        self.assertEqual(task_text_0, 'Тестовый пост')

    def test_task_detail_pages_show_correct_context(self):
        """Шаблон task_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post_count'), 14)

    def test_home_page_show_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse(
            'posts:post_create'), kwargs={'post_id': self.post.pk})
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_home_page_show_correct_context_editpost(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = (self.authorized_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk})))
        # Словарь ожидаемых типов полей формы:
        # указываем, объектами какого класса должны быть поля формы
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                # Проверяет, что поле формы является экземпляром
                # указанного класса
                self.assertIsInstance(form_field, expected)

    def test_first_page_contains_ten_records_main_page(self):

        page_first = {
            reverse('posts:main'),
            reverse(
                'posts:profile', kwargs={'username': self.author.username}),
        }

        page_second = {
            reverse('posts:main') + '?page=2',
            reverse(
                'posts:profile', kwargs={
                    'username': self.author.username}) + '?page=2',
        }
        for address in page_first:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(len(response.context['page_obj']), 10)

        for address in page_second:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(len(response.context['page_obj']), 4)

    def test_first_page_contains_ten_records_group(self):
        response = (self.authorized_author.get(
            reverse('posts:group', kwargs={'slug': self.group.slug})))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_first_page_contains_ten_records_group_second(self):
        response = (self.authorized_author.get(
            reverse('posts:group', kwargs={
                'slug': self.group.slug}) + '?page=2'))
        self.assertEqual(len(response.context['page_obj']), 3)
