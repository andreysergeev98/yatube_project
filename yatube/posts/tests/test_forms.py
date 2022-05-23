import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTest(TestCase):
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
            group=cls.group

        )

        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_create_post(self):
        tasks_count = Post.objects.count()
        form_data = {
            'author': self.author,
            'text': 'Тестовый заголовок',
            'group': f'{self.group.pk}',
        }

        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )

        self.assertEqual(Post.objects.count(), tasks_count + 1)

        response = (self.authorized_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk})))

        self.assertIn("text", response.context['form'].fields)
        self.assertIn("group", response.context['form'].fields)
        self.assertEqual(len(response.context['form'].fields), 2)

        self.assertTrue(
            Post.objects.filter(
                group=self.group.pk,
                text='Тестовый заголовок',
            ).exists()
        )

    def test_edit_post(self):
        tasks_count = Post.objects.count()
        form_data = {
            'author': self.author,
            'text': 'Тестовый заголовок отредактированный',
            'group': f'{self.group.pk}',
        }

        self.authorized_author.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )

        response = (self.authorized_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk})))

        self.assertIn("text", response.context['form'].fields)
        self.assertIn("group", response.context['form'].fields)
        self.assertEqual(len(response.context['form'].fields), 2)

        self.assertEqual(Post.objects.count(), tasks_count)

        self.assertTrue(
            Post.objects.filter(
                group=self.group.pk,
                text='Тестовый заголовок отредактированный',
            ).exists()
        )
