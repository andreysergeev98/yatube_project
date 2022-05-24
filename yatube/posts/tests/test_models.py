from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа adwad',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост с описанием',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост с описанием',
        )

    def test_models_have_correct_object_names(self):
        post = self.post
        self.assertEqual(str(post), self.post.text[:15])

        group = self.group
        self.assertEqual(str(group), self.group.title)
