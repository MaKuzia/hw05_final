from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

from posts.models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user_author = User.objects.create_user(username='AuthUser')
        cls.just_user = User.objects.create_user(username='JustUser')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user_author,
            text='Тестовый пост (*^▽^*)',
        )

    def setUp(self):
        self.authorized_author = Client()
        self.authorized_author.force_login(self.user_author)
        self.guest_client = Client()
        self.authorized_user = Client()
        self.authorized_user.force_login(self.just_user)

    def test_public_url_templates(self):
        """ Проверка общедоступных страниц"""

        public_url = {'/': 'posts/index.html',

                      f'/group/{self.group.slug}/':
                      'posts/group_list.html',

                      f'/posts/{self.post.pk}/':
                      'posts/post_detail.html',

                      f'/profile/{self.post.author.username}/':
                      'posts/profile.html',

                      }
        for url, template in public_url.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)

    def test_url_redirect_for_guest_client(self):
        """ Проверка редиректов для неавторизованного пользователя"""

        url_redirect = (
            '/create/',
            f'/posts/{self.post.pk}/edit/',
            f'/posts/{self.post.pk}/comment/',
        )
        for url in url_redirect:
            with self.subTest(url=url):
                response = self.guest_client.get(url, follow=True)
                self.assertRedirects(
                    response, ('/auth/login/?next=' + url)
                )

    def test_url_template_for_authorized_client(self):
        """ Проверка доступности страницы create_post.html'
            для авторизованного пользователя"""

        response = self.authorized_user.get('/create/')
        self.assertEqual(
            response.status_code, HTTPStatus.OK
        )
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_authorized_client_cant_use_edit(self):
        """Проверка НЕ доступности post_edit
            для авторизованного пользователя"""

        response = self.authorized_user.get(
            f'/posts/{self.post.pk}/edit/'
        )
        self.assertTemplateNotUsed(response, 'posts/create_post.html')

    def test_url_template_for_authorized_author(self):
        """ Проверка доступности post_edit для автора """

        response = self.authorized_author.get(
            f'/posts/{self.post.pk}/edit/'
        )
        self.assertEqual(response.status_code, HTTPStatus.OK)
        self.assertTemplateUsed(response, 'posts/create_post.html')

    def test_nonexistent_url(self):
        """Несуществующая страница"""

        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')
