import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)
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

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_create_post(self):
        posts_count = Post.objects.count()

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
        image_path = 'posts/' + str(uploaded)
        text_post = 'dwadawdawd'
        form_data = {
            'text': text_post,
            'image': uploaded,
            'group': self.group.pk,
        }

        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post_last = Post.objects.latest('id')
        self.assertEqual(post_last.text, text_post)
        self.assertEqual(post_last.group, self.group)
        self.assertTrue(post_last.image, image_path)

        response = (self.authorized_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk})))
        self.assertIn("text", response.context['form'].fields)
        self.assertIn("group", response.context['form'].fields)
        self.assertEqual(len(response.context['form'].fields), 3)

    def test_edit_post(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small_copy.gif',
            content=small_gif,
            content_type='image/gif'
        )
        image_path = 'posts/' + str(uploaded)
        text_edit = 'Тестовый заголовок отредактированный'
        form_data = {
            'text': text_edit,
            'group': self.group.pk,
            'image': uploaded,
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
        self.assertEqual(len(response.context['form'].fields), 3)
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.get(
                pk=self.post.pk,
                text=text_edit,
                group=self.group.pk,
                image=image_path
            )
        )

    def test_create_comment_to_post(self):
        comments_count = Comment.objects.count()
        text_comment = 'тестовый комментарий новый'
        form_data = {
            'text': text_comment,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Comment.objects.count(), comments_count + 1)

        response = (self.authorized_author.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.pk})))
        self.assertEqual(len(response.context['comments']), 1)
        comment_last = Comment.objects.latest('id')
        self.assertEqual(comment_last.text, text_comment)
        self.assertEqual(comment_last.post.pk, self.post.pk)
