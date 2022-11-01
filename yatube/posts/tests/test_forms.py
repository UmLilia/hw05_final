from django.test import Client, TestCase
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Post, Group, User
from posts.tests.test_urls import URL_CREATE


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='post_author')
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

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_create_post(self):
        """Валидная форма создает запись в Post."""
        url_profile = reverse(
            'posts:profile',
            kwargs={'username': PostCreateFormTests.user}
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост_1',
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            URL_CREATE,
            data=form_data,
            follow=True
        )
        first_obj = Post.objects.all().first()
        self.assertEqual(first_obj.group.id, self.group.id)
        self.assertEqual(first_obj.text, 'Тестовый пост_1')
        self.assertRedirects(response, url_profile)
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_edit_post(self):
        """Валидная форма вносит изменения в Post."""
        url_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': PostCreateFormTests.post.id}
        )
        url_post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostCreateFormTests.post.id}
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост_2',
            'group': self.group.id,
        }
        response = self.post_author.post(
            url_edit,
            data=form_data,
            follow=True
        )
        first_obj = Post.objects.all().first()
        self.assertEqual(first_obj.group.id, self.group.id)
        self.assertEqual(first_obj.text, 'Тестовый пост_2')
        self.assertRedirects(response, url_post_detail)
        self.assertEqual(Post.objects.count(), posts_count)
