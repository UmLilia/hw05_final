import shutil
import tempfile

from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.forms import PostForm
from posts.models import Post, Group, User
from posts.tests.test_urls import URL_INDEX, URL_CREATE

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x02\x00'
    b'\x01\x00\x80\x00\x00\x00\x00\x00'
    b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
    b'\x00\x00\x00\x2C\x00\x00\x00\x00'
    b'\x02\x00\x01\x00\x00\x02\x02\x0C'
    b'\x0A\x00\x3B'
)

UPLOADED = SimpleUploadedFile(
    name='small.gif',
    content=SMALL_GIF,
    content_type='image/gif'
)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostMediaTests(TestCase):
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
        cls.image = UPLOADED
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            group=cls.group,
            image=cls.image
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.post_author = Client()
        self.post_author.force_login(self.author)

    def test_create_post_img(self):
        """Валидная форма с картинкой создает запись в Post."""
        url_profile = reverse(
            'posts:profile',
            kwargs={'username': PostMediaTests.user}
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Тестовый пост_img',
            'group': self.group.id,
            'image': SMALL_GIF,
        }
        response = self.authorized_client.post(
            URL_CREATE,
            data=form_data,
            follow=True
        )
        first_obj = Post.objects.all().first()
        self.assertEqual(first_obj.text, 'Тестовый пост_img')
        self.assertRedirects(response, url_profile)
        self.assertEqual(Post.objects.count(), posts_count + 1)

    def test_page_with_image_context(self):
        """При выводе поста с картинкой изображение передаётся
        в словаре context"""
        url_group_list = reverse(
            'posts:group_list',
            kwargs={'slug': PostMediaTests.group.slug}
        )
        url_profile = reverse(
            'posts:profile',
            kwargs={'username': PostMediaTests.author}
        )
        url_post_detail = reverse(
            'posts:post_detail',
            kwargs={'post_id': PostMediaTests.post.id}
        )
        pages = (
            URL_INDEX,
            url_group_list,
            url_profile,
            url_post_detail
        )
        for page in pages:
            with self.subTest(page=page):
                response = self.post_author.get(page)
                context_image = response.context.get('post').image
                self.assertEqual(context_image, 'posts/small.gif')
