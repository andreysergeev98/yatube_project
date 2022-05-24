from django import forms
from django.conf import settings
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
            text='Тестовый пост первый',
            group=cls.group
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост второй',
            group=cls.group
        )
        for index in range(settings.PAGINATOR_PAGE):
            cls.index = Post.objects.create(
                author=cls.author,
                text='Тестовый пост',
                group=cls.group
            )

    def setUp(self):
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
        }
        urls_status_code_auth = {
            'posts/create_post.html': reverse('posts:post_create')
        }
        urls_status_code_author = {
            'posts/create_post.html': reverse(
                'posts:post_edit', kwargs={'post_id': self.post.pk}),
        }
        for template, address in urls_status_code.items():
            with self.subTest(address=address):
                response = self.client.get(address)
                self.assertTemplateUsed(response, template)

        for template, address in urls_status_code_auth.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)

        for template, address in urls_status_code_author.items():
            with self.subTest(address=address):
                response = self.authorized_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_post_detail_pages_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = (self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})))
        self.assertEqual(response.context.get('post').text, self.post.text)
        self.assertEqual(response.context.get('post').pk, self.post.pk)

    def test_home_page_show_correct_context(self):
        """Шаблон home сформирован с правильным контекстом."""
        response = self.authorized_author.get(reverse(
            'posts:post_create'), kwargs={'post_id': self.post.pk})
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
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.models.ModelChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_first_page_contains_ten_records_main_page(self):
        page_first = {
            reverse('posts:main'),
            reverse(
                'posts:profile', kwargs={'username': self.author.username}),
            reverse('posts:group', kwargs={'slug': self.group.slug})
        }
        page_second = {
            reverse('posts:main') + '?page=2',
            reverse(
                'posts:profile', kwargs={
                    'username': self.author.username}) + '?page=2',
            reverse('posts:group', kwargs={
                'slug': self.group.slug}) + '?page=2'
        }
        for address in page_first:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']), settings.PAGINATOR_PAGE
                )
        for address in page_second:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(len(response.context['page_obj']), 2)

    def test_comment_add(self):
        form_data = {
            'text': 'новый коммент'
        }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        response = (self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})))
        self.assertEqual(response.context['comments'].count(), 1)

    def test_create_post(self):
        form_data = {
            'author': self.author,
            'text': 'dwadawdawd',
            'group': self.group.pk,
        }
        self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        page_second = {
            reverse('posts:main') + '?page=2',
            reverse('posts:group', kwargs={
                'slug': self.group.slug}) + '?page=2',
            reverse('posts:profile', kwargs={
                'username': self.author.username}) + '?page=2'
        }
        for address in page_second:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertEqual(
                    len(response.context['page_obj']),
                    Post.objects.count() - settings.PAGINATOR_PAGE
                )
        self.assertEqual(Post.objects.order_by('pk').last().group, self.group)
