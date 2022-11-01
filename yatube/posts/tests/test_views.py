from django.test import Client, TestCase
from django.urls import reverse
from django import forms
from django.core.cache import cache

from posts.models import Post, Group, User, Follow
from posts.tests.test_urls import URL_INDEX, URL_CREATE, URL_FOLLOW


class PostPagesTests(TestCase):
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

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_group_list = reverse(
            'posts:group_list',
            kwargs={'slug': PostPagesTests.group.slug}
        )
        url_profile = reverse(
            'posts:profile',
            kwargs={'username': PostPagesTests.user}
        )
        url_post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostPagesTests.post.id}
        )
        url_post_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': PostPagesTests.post.id}
        )
        templates_pages_names = {
            URL_INDEX: 'posts/index.html',
            url_group_list: 'posts/group_list.html',
            url_profile: 'posts/profile.html',
            url_post_detail: 'posts/post_detail.html',
            url_post_edit: 'posts/create.html',
            URL_CREATE: 'posts/create.html'
        }
        for reverse_name, template in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.post_author.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_list_page_show_correct_context(self):
        """Шаблон сформирован с правильным контекстом."""
        url_group_list = reverse(
            'posts:group_list',
            kwargs={'slug': PostPagesTests.group.slug}
        )
        url_profile = reverse(
            'posts:profile',
            kwargs={'username': PostPagesTests.author}
        )
        pages = (
            URL_INDEX,
            url_group_list,
            url_profile
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.post_author.get(page)
                first_object = response.context['page_obj'][0]
                post_author = first_object.author.username
                post_text = first_object.text
                post_group = first_object.group.title
                self.assertEqual(post_author, 'post_author')
                self.assertEqual(post_text, 'Тестовый пост')
                self.assertEqual(post_group, 'Тестовая группа')

    def test_post_detail_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        url_post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostPagesTests.post.id}
        )
        response = self.authorized_client.get(url_post_detail)
        self.assertEqual(
            response.context.get('post').text,
            PostPagesTests.post.text
        )
        self.assertEqual(
            response.context.get('post').author,
            PostPagesTests.post.author
        )
        self.assertEqual(
            response.context.get('post').group,
            PostPagesTests.post.group
        )

    def test_form_show_correct_context(self):
        """Шаблон form сформирован с правильным контекстом."""
        url_post_edit = reverse(
            'posts:post_edit',
            kwargs={'post_id': PostPagesTests.post.id}
        )
        response_1 = self.post_author.get(URL_CREATE)
        response_2 = self.post_author.get(url_post_edit)
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field_1 = response_1.context.get('form').fields.get(value)
                form_field_2 = response_2.context.get('form').fields.get(value)
                self.assertIsInstance(form_field_1, expected)
                self.assertIsInstance(form_field_2, expected)

    
    def test_cache(self):
        """При удалении записи из базы, она остаётся в response.content."""
        first_content = self.authorized_client.get(URL_INDEX).content
        Post.objects.get(id=PostPagesTests.post.id).delete()
        content_2 = self.authorized_client.get(URL_INDEX).content
        self.assertEqual(first_content, content_2)
        cache.clear()
        content_3 = self.authorized_client.get(URL_INDEX).content
        self.assertNotEqual(first_content, content_3)

    def test_follow(self):
        """Авторизованный пользователь может подписываться на других пользователей 
        и удалять их из подписок."""
        url_follow_profile = reverse(
            'posts:profile_follow',
            kwargs={'username': PostPagesTests.author}
        )
        url_unfollow_profile = reverse(
            'posts:profile_unfollow',
            kwargs={'username': PostPagesTests.author}
        )
        self.authorized_client.post(url_follow_profile)
        self.assertEqual(len(Follow.objects.all()), 1)
        self.authorized_client.post(url_unfollow_profile)
        self.assertEqual(len(Follow.objects.all()), 0)

    def test_follow_post(self):
        """Новая запись пользователя появляется в ленте тех, кто на него подписан 
        и не появляется в ленте тех, кто не подписан."""
        url_follow_profile = reverse(
            'posts:profile_follow',
            kwargs={'username': PostPagesTests.author}
        )
        self.authorized_client.post(url_follow_profile)
        self.post_author.post(
            URL_CREATE,
            data={'text': 'Тест подписок!'}
        )
        self.assertContains(
            self.authorized_client.get(URL_FOLLOW),
            'Тест подписок!'
        )
        self.assertNotContains(
            self.post_author.get(URL_FOLLOW),
            'Тест подписок!'
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = []
        for i in range(13):
            cls.post.append(Post(
                author=cls.user,
                text=f'Тестовый пост{i}',
                group=cls.group
            ))
        Post.objects.bulk_create(cls.post)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_page_contains_ten_records(self):
        """Проверка: количество постов на первой странице равно 10."""
        url_group_list = reverse(
            'posts:group_list',
            kwargs={'slug': PaginatorViewsTest.group.slug}
        )
        url_profile = reverse(
            'posts:profile',
            kwargs={'username': PaginatorViewsTest.user}
        )
        pages = (
            URL_INDEX,
            url_group_list,
            url_profile
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_contains_three_records(self):
        """Проверка: на второй странице должно быть три поста."""
        url_group_list = reverse(
            'posts:group_list',
            kwargs={'slug': PaginatorViewsTest.group.slug}
        )
        url_profile = reverse(
            'posts:profile',
            kwargs={'username': PaginatorViewsTest.user}
        )
        pages = (
            URL_INDEX,
            url_group_list,
            url_profile
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.authorized_client.get(page + '?page=2')
                self.assertEqual(len(response.context['page_obj']), 3)


class PostGroupTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='user')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа_1',
            slug='test-slug_1',
            description='Тестовое описание_1',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа_2',
            slug='test-slug_2',
            description='Тестовое описание_2',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост',
            group=cls.group_1
        )

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def group_test(self):
        """Пост появляется на верных страницах и присваивает верную группу"""
        url_group1_list = reverse(
            'posts:group_list',
            kwargs={'slug': PostGroupTests.group_1.slug}
        )
        url_group2_list = reverse(
            'posts:group_list',
            kwargs={'slug': PostGroupTests.group_2.slug}
        )
        url_profile = reverse(
            'posts:profile',
            kwargs={'username': PostGroupTests.user.username}
        )
        pages = {
            URL_INDEX: 'Тестовый пост',
            url_group1_list: 'Тестовый пост',
            url_group2_list: None,
            url_profile: 'Тестовый пост'
        }
        for page, text in pages.items():
            with self.subTest(page=page):
                response = self.authorized_client.get(page)
                self.assertEqual(response.context.get('post').text, text)
