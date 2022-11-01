from django.test import TestCase, Client
from django.urls import reverse

from posts.models import Post, User


class CommentTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.author = User.objects.create_user(username='post_author')
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_comments_only_for_authorized(self):
        """Комментировать посты может только авторизованный пользователь."""
        url_comment = reverse(
            'posts:add_comment',
            kwargs={'post_id': CommentTests.post.id}
        )
        url_post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': CommentTests.post.id}
        )
        self.guest_client.post(
            url_comment,
            data={'text': 'Новый коммент!'}
        )
        self.authorized_client.post(
            url_comment,
            data={'text': 'Новый коммент_1!'}
        )
        response = self.authorized_client.get(url_post_detail)
        self.assertContains(response, 'Новый коммент_1!')
        self.assertNotContains(response, 'Новый коммент!')
