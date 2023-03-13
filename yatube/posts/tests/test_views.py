from http import HTTPStatus
from django.contrib.auth import get_user_model
from django.test import TestCase, Client
from django import forms
from ..models import Post, Group, Comment
from django.urls import reverse

User = get_user_model()


class PostPagesTests(TestCase):
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

    def setUp(self):
        # Создаем неавторизованный клиент
        self.guest_client = Client()
        # Создаем авторизованный клиент
        self.authorized_client = Client()
        # Авторизуем пользователя
        self.authorized_client.force_login(self.user)

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон и HTTP статус."""
        templates_page_names = {
            reverse('posts:group_list', kwargs={'slug': self.group.slug}): (
                'posts/group_list.html'
            ),
            reverse('posts:index'): 'posts/index.html',
            reverse('posts:profile', kwargs={'username': (
                self.user.username)}): 'posts/profile.html',
            reverse('posts:post_create'): 'posts/create_post.html',
            reverse('posts:post_detail', kwargs={'post_id': (
                self.post.pk)}): 'posts/post_detail.html',
            reverse('posts:post_edit', kwargs={'post_id': (
                self.post.pk)}): 'posts/create_post.html',
        }
        for reverse_name, template in templates_page_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_posts_show_correct_context(self):
        """Шаблоны posts сформированы с правильным контекстом."""
        namespace_list = {
            reverse('posts:index'): 'page_obj',
            reverse('posts:group_list', args=[self.group.slug]): 'page_obj',
            reverse('posts:profile', args=[self.user.username]): 'page_obj',
            reverse('posts:post_detail', args=[self.post.pk]): 'post',
        }
        for reverse_name, context in namespace_list.items():
            first_object = self.guest_client.get(reverse_name)
            if context == 'post':
                first_object = first_object.context[context]
            else:
                first_object = first_object.context[context][0]
            post_text = first_object.text
            post_author = first_object.author
            post_group = first_object.group
            posts_dict = {
                post_text: self.post.text,
                post_author: self.user,
                post_group: self.group,
            }
            for post_param, test_post_param in posts_dict.items():
                with self.subTest(
                        post_param=post_param,
                        test_post_param=test_post_param):
                    self.assertEqual(post_param, test_post_param)

    def test_create_post_show_correct_context(self):
        """Шаблоны create и edit сформированы с правильным контекстом."""
        namespace_list = [
            reverse('posts:post_create'),
            reverse('posts:post_edit', args=[self.post.pk])
        ]
        for reverse_name in namespace_list:
            response = self.authorized_client.get(reverse_name)
            form_fields = {
                'text': forms.fields.CharField,
                'group': forms.fields.ChoiceField,
            }
            for value, expected in form_fields.items():
                with self.subTest(value=value):
                    form_field = response.context['form'].fields[value]
                    self.assertIsInstance(form_field, expected)

    def test_post_another_group(self):
        """Пост не попал в другую группу"""
        response = self.authorized_client.get(
            reverse('posts:group_list', args={self.group.slug}))
        first_object = response.context["page_obj"][0]
        post_text = first_object.text
        self.assertTrue(post_text, 'Тестовый текст')


class CommentViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.auth_user = User.objects.create_user(username='auth_user')
        cls.group = Group.objects.create(
            title='Тестовый заголовок',
            description='Описание',
            slug='test-slug'
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
            pub_date='Дата публикации',
            group=cls.group,
        )

        cls.guest_client = Client()
        cls.authorized_auth = Client()
        cls.authorized_auth.force_login(cls.author)

    def test_add_comment_for_guest(self):
        response = self.guest_client.get(
            reverse(
                'posts:add_comment',
                kwargs={
                    'post_id': self.post.id
                }
            )
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.FOUND,
            ('Не авторизированный пользователь'
             ' не может оставлять комментарий')
        )

    def test_comment_available(self):
        post = CommentViewsTest.post
        client = self.authorized_auth
        response = client.get(
            reverse(
                'posts:post_detail',
                kwargs={
                    'post_id': post.id
                }
            )
        )
        self.assertEqual(
            response.status_code,
            HTTPStatus.OK,
            ('Авторизированный пользователь'
             ' должен иметь возможность'
             ' оставлять комментарий')
        )
        comments_count = Comment.objects.filter(
            post=post.id
        ).count()
        form_data = {
            'text': 'test_comment',
        }

        response = client.post(
            reverse('posts:post_detail',
                    kwargs={
                        'post_id': post.id
                    }
                    ),
            data=form_data,
            follow=True
        )
        comments = Post.objects.filter(
            id=post.id
        ).values_list('comments', flat=True)
        self.assertEqual(
            comments.count(),
            comments_count + 1)
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertFalse(Comment.objects.filter(
            text='test_comment').exists())
