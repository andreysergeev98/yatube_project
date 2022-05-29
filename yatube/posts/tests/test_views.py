import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostViewTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
        cls.user = User.objects.create_user(username='testnoname')
        cls.author = User.objects.create_user(username='auth')
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.image = SimpleUploadedFile(
            name='small_test.gif',
            content=cls.small_gif,
            content_type='image/gif',
        )

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
            image=cls.image,
            group=cls.group
        )

        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост второй',
            image=cls.image,
            group=cls.group
        )
        for index in range(settings.PAGINATOR_PAGE):
            cls.index = Post.objects.create(
                author=cls.author,
                text='Тестовый пост',
                image=cls.image,
                group=cls.group
            )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_url_everyone_uses_correct_template(self):
        """Проверка шаблонов для общедоступных адресов."""
        cache.clear()
        urls_status_code = {
            'posts/index.html': reverse('posts:main'),
            'posts/group_list.html': reverse(
                'posts:group', kwargs={'slug': self.group.slug}),
            'posts/post_detail.html': reverse(
                'posts:post_detail', kwargs={'post_id': self.post.pk}),
        }
        urls_status_code_auth = {
            'posts/create_post.html': reverse('posts:post_create'),
            'posts/profile.html': reverse(
                'posts:profile', kwargs={'username': self.user.username}),
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
        """валидность типов формы из контекста при создании поста."""
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
        """валидность типов формы из контекста при редактировании поста."""
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
        cache.clear()
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

    def test_post_correct_context_with_image_field(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        cache.clear()
        page_first = {
            reverse('posts:main'),
            reverse(
                'posts:profile', kwargs={'username': self.author.username}),
            reverse(
                'posts:group', kwargs={'slug': self.group.slug}),
        }
        for address in page_first:
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTrue(response.context['page_obj'][0].image)

        response = (self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})))
        self.assertTrue(response.context['post'].image)

    def test_follow_correct_suscribe(self):
        follows_count = Follow.objects.count()
        (self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username})))
        self.assertEqual(Follow.objects.count(), follows_count + 1)

        (self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author.username})))
        self.assertEqual(Follow.objects.count(), follows_count)

    def test_followig_page(self):
        """Страница Подписок на авторов."""
        (self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username})))
        form_data = {
            'author': self.author,
            'text': 'post for subscribe',
            'group': self.group.pk,
        }
        self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response = (self.authorized_client.get(reverse(
            'posts:follow_index') + '?page=2'))
        self.assertEqual(len(response.context['page_obj']), 3)

        response = (self.authorized_author.get(reverse(
            'posts:follow_index')))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_caching_page(self):
        """Проверка кэширование на главной странице."""
        cache.clear()
        response_old = self.client.get(reverse('posts:main'))
        form_data = {
            'author': self.author,
            'text': 'test post cache removed',
            'group': self.group.pk,
        }
        self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        response = self.client.get(reverse('posts:main'))
        Post.objects.latest('id').delete()
        (self.assertEqual(response.content,
         self.client.get(reverse('posts:main')).content))
        cache.clear()
        (self.assertEqual(response_old.content,
         self.client.get(reverse('posts:main')).content))
