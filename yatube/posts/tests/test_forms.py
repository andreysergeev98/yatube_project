from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


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

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author = Client()
        self.authorized_author.force_login(self.author)

    def test_create_post(self):
        posts_count = Post.objects.count()
        form_data = {
            'text': 'dwadawdawd',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), posts_count + 1)
        post_create = response.context['page_obj'][0]
        post_last = Post.objects.latest('pub_date')
        self.assertEqual(post_last.pk, post_create.pk)
        self.assertEqual(post_last.text, post_create.text)
        self.assertEqual(post_last.group, post_create.group)

        response = (self.authorized_author.get(reverse(
            'posts:post_edit', kwargs={'post_id': self.post.pk})))
        self.assertIn("text", response.context['form'].fields)
        self.assertIn("group", response.context['form'].fields)
        self.assertEqual(len(response.context['form'].fields), 2)

    def test_edit_post(self):
        posts_count = Post.objects.count()
        text_edit = 'Тестовый заголовок отредактированный'
        form_data = {
            'text': text_edit,
            'group': self.group.pk,
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
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertTrue(
            Post.objects.get(
                pk=self.post.pk,
                text=text_edit,
                group=self.group.pk
            )
        )
