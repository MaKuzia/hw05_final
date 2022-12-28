from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='Тестовый слаг',
            description='Тестовое описание',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый пост (*^▽^*)',
        )

    def test_models_group_have_correct_object_names(self):
        """корректно работает __str__."""

        for_check_str = {
            self.group: self.group.title,
            self.post: self.post.text[:15]
        }
        for model, expecting in for_check_str.items():
            with self.subTest(model=model):
                self.assertEqual(str(model), expecting)

    def test_verbose_name(self):
        """verbose_name в полях совпадает с ожидаемым."""

        group_verboses = {
            'title': 'Название группы',
            'slug': 'Уникальный адрес группы',
            'description': 'Описание',
        }
        for field, expected_value in group_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.group._meta.get_field(field).verbose_name,
                    expected_value)

        post_verboses = {
            'text': 'Пост',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }
        for field, expected_value in post_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    self.post._meta.get_field(field).verbose_name,
                    expected_value)
