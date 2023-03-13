import shutil
import tempfile
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from ..models import Group, Post, User
from ..forms import PostForm

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create(username='TestUser')
        cls.group = Group.objects.create(
            title='Группа',
            description='Описание поста',
            slug='test-slug',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Текст поста',
        )


class PostFormsTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='TestUser')
        cls.group = Group.objects.create(
            title="Тестовая заголовок",
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            text='Тестовый текст',
            pub_date='Тестовая дата',
            author=cls.user,
            group=cls.group,
        )
        cls.form = PostForm()
        cls.authorized_client = Client()
        cls.second_authorized_client = Client()
        cls.form_data = {
            'text': f'{cls.post.text}',
            'group': f'{cls.group.id}',
        }

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

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
        form_data = {
            'group': self.group.pk,
            'text': self.post.text,
            'image': uploaded,
        }
        response = self.author_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={
                'username': PostCreateFormTests.post.author
            }))
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group=self.group,
                text=self.post.text,
                image=self.post.image,
            ).exists()
        )

    def test_authorized_client_post_create(self):
        """Создается новая запись в базе
        данных авторизованным пользователем."""
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Данные из формы',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        last_obj = Post.objects.all().last()
        self.assertEqual(last_obj.text, 'Тестовый текст')
        self.assertEqual(last_obj.author, self.user)
        self.assertEqual(last_obj.group, self.group)
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertRedirects(response, reverse(
            'posts:profile',
            kwargs={'username': self.user.username}))

    def test_authorized_post_edit(self):
        """"Авторизованный клиент может редактировать посты."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Измененный текст',
            'group': self.group.pk,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertRedirects(
            response, f'/posts/{self.post.id}/edit/'
        )

    def test_guest_client_post_create(self):
        """"Анонимный гость не может создавать посты."""
        form_data = {
            'text': 'Пост от неавторизованного клиента',
            'group': self.group.id
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertFalse(Post.objects.filter(
            text='Пост от неавторизованного клиента').exists())

    def test_guest_can_not_edit_post(self):
        """Анонимный гость не может редактировать посты
        и перенаправляется на страницу логина"""
        response = self.guest_client.post(
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'}),
            data=self.form_data,
            follow=True
        )
        self.assertRedirects(
            response, f'/auth/login/?next=/posts/{self.post.id}/edit/'
        )

    def test_users_can_not_edit_post(self):
        """Не авторы не могут изменять чужие посты."""
        response = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': f'{self.post.id}'}),
            data=self.form_data,
            follow=True
        )
        self.assertRedirects(
            response, f'/posts/{self.post.id}/edit/'
        )
