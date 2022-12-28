import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import CommentForm, PostForm
from posts.models import Comment, Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostsPagesTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='AuthUser')
        cls.just_user = User.objects.create_user(username='JustUser')
        cls.user_without = User.objects.create_user(username='WithoutFollow')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            group=cls.group,
            author=cls.user_author,
            text='Тестовый пост (*^▽^*)',
            image=cls.uploaded
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.just_user,
            text='Тестовый комментарий'
        )
        cls.follow = Follow.objects.create(
            user=cls.just_user,
            author=cls.user_author
        )

        cls.info = {'index': ['posts:index', None, 'posts/index.html'],
                    'group_list': ['posts:group_list', (cls.group.slug,),
                                   'posts/group_list.html'],
                    'profile': ['posts:profile', (cls.user_author.username,),
                                'posts/profile.html'],
                    'p_detail': ['posts:post_detail', (cls.post.id,),
                                 'posts/post_detail.html'],
                    'p_create': ['posts:post_create', None,
                                 'posts/create_post.html'],
                    'p_edit': ['posts:post_edit', (cls.post.id,),
                               'posts/create_post.html'],
                    'follow': ['posts:follow_index', None, 'posts/follow.html']
                    }

        cls.url_for_tests = [
            reverse(cls.info['index'][0]),
            reverse(cls.info['group_list'][0],
                    args=cls.info['group_list'][1]),
            reverse(cls.info['profile'][0],
                    args=cls.info['profile'][1]),
            reverse(cls.info['follow'][0])
        ]

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user_author)
        self.authorized_user = Client()
        self.authorized_user.force_login(self.just_user)
        self.user_without_follow = Client()
        self.user_without_follow.force_login(self.user_without)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """ В view-функциях используются правильные html-шаблоны"""
        cache.clear()
        for reverse_name, args, templates in self.info.values():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_author.get(reverse(reverse_name,
                                                              args=args))
                self.assertTemplateUsed(response, templates)

    def correct_value_fields_post(self, response):
        self.assertEqual(response.group, self.post.group)
        self.assertEqual(response.author, self.post.author)
        self.assertEqual(response.text, self.post.text)
        self.assertEqual(response.image, self.post.image)

    def test_post_detail_pages_show_correct_context(self):
        """тестирование context в post_detail c comments)"""

        response = (self.authorized_user.get(reverse(self.info['p_detail'][0],
                    args=self.info['p_detail'][1])))

        self.correct_value_fields_post(response.context.get('post'))
        self.assertEqual(response.context.get('comments').last(), self.comment)
        self.assertEqual(response.context.get('form').__class__, CommentForm)

    def test_post_create_show_correct_context(self):
        """тестирование context при создании/редактировании поста"""
        url_ = [
            reverse(self.info['p_create'][0]),
            reverse(self.info['p_edit'][0],
                    args=self.info['p_edit'][1])
        ]
        for url in url_:
            with self.subTest(url=url):
                response = self.authorized_author.get(url)
                self.assertEqual(response.context.get('form').__class__,
                                 PostForm)
                if url == url_[0]:
                    self.assertIsNone(response.context.get('is_edit'))
                else:
                    self.assertTrue(response.context.get('is_edit'))
                form_fields = {
                    'text': forms.fields.CharField,
                    'group': forms.fields.ChoiceField,
                    'image': forms.ImageField,
                }
                for value, expected in form_fields.items():
                    with self.subTest(value=value):
                        form_field = response.context.get('form').fields.get(
                            value)
                        self.assertIsInstance(form_field, expected)

    def test_first_page_contains_ten_records(self):
        """
        тестирование context:
            - на главной странице сайта,
            - на странице выбранной группы,
            - в профайле пользователя
            - страница с пдписками на авторов
            """

        for url in self.url_for_tests:
            with self.subTest(url=url):
                response = self.authorized_user.get(url)
                if (self.assertIn('page_obj', response.context)
                    and self.assertGreaterEqual(
                        response.context['page_obj'], 1)):
                    self.correct_value_fields_post(
                        response.context['page_obj'][0]
                    )
                if url == self.url_for_tests[1]:
                    self.assertEqual(response.context.get('group'),
                                     self.post.group)
                elif url == self.url_for_tests[2]:
                    self.assertEqual(response.context.get('author'),
                                     self.post.author)

    def test_paginator(self):
        """ Тестирование паджинатора"""

        count_of_test_posts = 11

        for i in range(count_of_test_posts):
            Post.objects.create(
                group=self.group,
                author=self.user_author,
                text='Тестовый пост',
                image=self.uploaded)

        for url in self.url_for_tests:
            with self.subTest(url=url):
                response = self.authorized_user.get(url)
                self.assertEqual(len(response.context['page_obj']),
                                 settings.POSTS_PER_PAGE)
                response = self.authorized_user.get(url + '?page=2')
                self.assertEqual(len(response.context['page_obj']),
                                 Post.objects.count() - settings.POSTS_PER_PAGE
                                 )

    def test_delete_comment(self):
        """Отписка от автора"""

        self.follow.delete()
        response = self.authorized_user.get(reverse(self.info['follow'][0]))
        self.assertEqual(len(response.context['page_obj']), 0)

    def test_page_of_follow(self):
        """
        Новая запись пользователя появляется в ленте тех,
            кто на него подписан и не появляется в ленте тех,
            кто не подписан.
        """
        users = (
            self.authorized_user,
            self.user_without_follow
        )
        for user in users:
            response = user.get(reverse(self.info['follow'][0]))
            posts_count = len(response.context['page_obj'])
            Post.objects.create(
                group=self.group,
                author=self.user_author,
                text='Тестовый пост',
                image=self.uploaded
            )
            response = user.get(reverse(self.info['follow'][0]))
            if user == self.authorized_user:
                self.assertEqual(len(response.context['page_obj']),
                                 posts_count + 1)
            else:
                self.assertEqual(
                    len(response.context['page_obj']), posts_count
                )


class IndexFormCacheTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.just_user = User.objects.create_user(username='JustUser')

        cls.post = Post.objects.create(
            author=cls.just_user,
            text='Тестовый пост',
        )

    def setUp(self):
        self.user = Client()
        self.user.force_login(self.just_user)
        cache.clear()

    def test_cache(self):

        response = self.user.get(reverse('posts:index'))
        posts_count = response.content

        self.post.delete

        response_2 = self.user.get(reverse('posts:index'))
        posts_count_2 = response_2.content

        self.assertEqual(posts_count, posts_count_2)
