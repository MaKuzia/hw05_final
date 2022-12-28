import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from posts.forms import PostForm
from posts.models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='AuthUser')
        cls.just_user = User.objects.create_user(username='JustUser')
        cls.group_1 = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group_2 = Group.objects.create(
            title='Тестовая группа_2',
            slug='edit-slug',
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
            author=cls.user_author,
            text='Тестовый пост (*^▽^*)',
            group=cls.group_1,
            image=cls.uploaded,
        )
        cls.form = PostForm()
        cls.posts_count = Post.objects.count()
        cls.comment_count = Comment.objects.count()

    @classmethod
    def tearDownClass(cls) -> None:
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author = Client()
        self.author.force_login(self.user_author)
        self.guest_client = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.just_user)

    def check_edited_created_post(self, some_post, some_user, path):

        response = some_user.post(
            path,
            data=some_post,
            follow=True,
        )

        for_checking = (
            [Post.objects.first().group.id, some_post['group']],
            [Post.objects.first().author, self.user_author],
            [Post.objects.first().text, some_post['text']],
            # [Post.objects.first().image, some_post['image']]
        )
        if path == reverse('posts:post_create'):
            self.assertEqual(Post.objects.count(), self.posts_count + 1)
            if some_user == self.author:
                self.assertEqual(response.status_code, HTTPStatus.OK)
                for post_field, some_post_field in for_checking:
                    with self.subTest(post_field=post_field):
                        self.assertEqual(post_field, some_post_field)
                    self.assertTrue(
                        Post.objects.filter(image='posts/small.gif').exists()
                    )
            else:
                self.assertRedirects(response, ('/auth/login/?next=/create/'))
        else:
            self.assertEqual(Post.objects.count(), self.posts_count)
            if some_user == self.guest_client:
                self.assertRedirects(response, (
                    f'/auth/login/?next=/posts/{Post.objects.first().id}/edit/'
                ))
            elif some_user == self.author:
                self.assertEqual(response.status_code, HTTPStatus.OK)
                for post_field, some_post_field in for_checking:
                    with self.subTest(post_field=post_field):
                        self.assertEqual(post_field, some_post_field)
                    self.assertTrue(
                        Post.objects.filter(image='posts/small.gif').exists()
                    )
            else:
                self.assertTemplateNotUsed(response, 'posts/create_post.html')

    def test_of_creating_post(self):
        """
        Создание новой записи в БД для:
                -авторизованного,
                -неавторизованного пользователей.
        """
        new_post = {
            'text': 'Тестовый пост (*^▽^*)',
            'group': self.group_1.id,
            'image': self.uploaded.name,
        }
        self.check_edited_created_post(new_post, self.author,
                                       reverse('posts:post_create'))
        self.check_edited_created_post(new_post, self.guest_client,
                                       reverse('posts:post_create'))

    def test_of_editing_post(self):
        """
        Редактирование записи в БД для:
                -авторизованного,
                -неавторизованного пользователей,
                -автора.
        """
        edit_post = Post.objects.first()
        edit_post = {
            'text': Post.objects.first().text,
            'group': self.group_2.id,
            'image': self.uploaded.name,
        }
        users = [
            self.author,
            self.authorized_user,
            self.guest_client
        ]
        for user in users:
            self.check_edited_created_post(edit_post, user,
                                           reverse('posts:post_edit',
                                                   args=(
                                                       Post.objects.first().id,
                                                   )
                                                   ))

    def test_checking_creating_comments_for_authorized_user(self):
        """Создание комментария авторизованным пользователем"""

        new_comment = {
            'text': 'Test comment!'
        }
        response = self.authorized_user.post(
            reverse('posts:add_comment', args=(Post.objects.first().id,)),
            data=new_comment,
            follow=True
        )
        for_checking = (
            [Comment.objects.first().post, Post.objects.first()],
            [Comment.objects.first().author, self.just_user],
            [Comment.objects.first().text, new_comment['text']],
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertEqual(Comment.objects.count(), self.comment_count + 1)
        for comment_field, expected_field in for_checking:
            with self.subTest(comment_field=comment_field):
                self.assertEqual(comment_field, expected_field)

    def test_checking_creating_comments_for_guest_client(self):
        """Создание комментария НЕ авторизованным пользователем"""

        new_comment = {
            'text': 'Test comment!'
        }
        response = self.guest_client.post(
            reverse('posts:add_comment', args=(Post.objects.first().id,)),
            data=new_comment,
            follow=True)
        self.assertRedirects(response, (
            f'/auth/login/?next=/posts/{Post.objects.first().id}/comment/')
        )
        self.assertEqual(Comment.objects.count(), self.comment_count)
