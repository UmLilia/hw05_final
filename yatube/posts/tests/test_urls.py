from django.test import TestCase, Client
from django.urls import reverse

from http import HTTPStatus

from posts.models import Post, Group, User

URL_INDEX = reverse('posts:index')
URL_LOGIN = reverse('users:login')
URL_CREATE = reverse('posts:create')
URL_FOLLOW = reverse('posts:follow_index')


class PostURLTests(TestCase):
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
        )

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_url_exists_at_desired_location_all(self):
        """Страница доступна любому пользователю."""
        url_profile = reverse(
            'posts:profile',
            kwargs={'username': PostURLTests.user}
        )
        url_group = reverse(
            'posts:group_list',
            kwargs={'slug': PostURLTests.group.slug}
        )
        url_post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostURLTests.post.id}
        )
        url_unexisting = 'unexisting_page'
        urls = {
            URL_INDEX: HTTPStatus.OK,
            url_group: HTTPStatus.OK,
            url_profile: HTTPStatus.OK,
            url_post_detail: HTTPStatus.OK,
            url_unexisting: HTTPStatus.NOT_FOUND
        }
        for address, status_code in urls.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertEqual(response.status_code, status_code)

    def test_url_exist_at_desired_location_author(self):
        """Страница posts/post_id/edit/ доступна автору."""
        url = reverse(
            'posts:post_edit',
            kwargs={'post_id': PostURLTests.post.id}
        )
        response = self.post_author.get(url)
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_exist_at_desired_location_authorized_client(self):
        """Страница доступна авторизованному пользователю."""
        urls = (
            URL_FOLLOW,
            URL_CREATE
        )
        for address in urls:
            with self.subTest(address=address):
                response = self.authorized_client.get(address, follow=True)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_url_redirect_anonymous(self):
        """Страница перенаправляет анонимного пользователя."""
        url_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': PostURLTests.post.id}
        )
        urls = (
            url_edit,
            URL_CREATE
        )
        for address in urls:
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(
                    response,
                    URL_LOGIN + '?next=' + address
                )

    def test_edit_url_redirect_authorized_client(self):
        """Страница edit перенаправляет авторизованного пользователя."""
        url_post_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': PostURLTests.post.id}
        )
        url_post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostURLTests.post.id}
        )
        response = self.authorized_client.get(url_post_edit, follow=True)
        self.assertRedirects(response, url_post_detail)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_profile = reverse(
            'posts:profile',
            kwargs={'username': PostURLTests.user}
        )
        url_group = reverse(
            'posts:group_list',
            kwargs={'slug': PostURLTests.group.slug}
        )
        url_post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostURLTests.post.id}
        )
        templates_url_names = {
            URL_INDEX: 'posts/index.html',
            url_group: 'posts/group_list.html',
            url_profile: 'posts/profile.html',
            url_post_detail: 'posts/post_detail.html',
            url_post_detail + 'edit/': 'posts/create.html',
            URL_CREATE: 'posts/create.html',
        }
        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.post_author.get(address)
                self.assertTemplateUsed(response, template)
