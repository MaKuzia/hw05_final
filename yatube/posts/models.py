from django.contrib.auth import get_user_model
from django.db import models

from core.models import CreateModel

User = get_user_model()


class Group(models.Model):
    """
    Модель для хранения групп.
    --------
    Атрибуты
    --------
    title: CharField
        название группы
    slug: SlugField
        уникальный адрес группы, часть URL
    description: TextFieldss
        текст, описывающий группу
    """

    title = models.CharField(
        max_length=200,
        verbose_name='Название группы'
    )
    slug = models.SlugField(
        max_length=200,
        unique=True,
        verbose_name='Уникальный адрес группы'
    )
    description = models.TextField(verbose_name='Описание')

    class Meta:
        verbose_name = 'Группы постов'
        verbose_name_plural = 'Группы постов'
        ordering = ('title',)

    def __str__(self):
        return f'{self.title}'


class Post(models.Model):
    """
    Модель для хранения постов.
    --------
    Атрибуты
    --------
    text: TextField
        текст поста
    pub_date: DateTimeField
        дата публикации поста
    author: ForeignKey
        автор поста
    group: ForeignKey
        группа поста
    """

    text = models.TextField(
        verbose_name='Пост',
        help_text='Содержание поста'
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата публикации'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        related_name='posts',
        verbose_name='Группа',
        help_text='Укажите группу (по желанию)'
    )
    image = models.ImageField(
        'Картинка',
        upload_to='posts/',
        blank=True,
        help_text='Вы можете загрузить изображение'
    )

    class Meta:
        verbose_name = 'Пост'
        verbose_name_plural = 'Посты'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'{self.text[:15]}'


class Comment(CreateModel):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Пост',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Автор комментария'
    )
    text = models.TextField(
        verbose_name='Комментарий',
        help_text='Место ввода комментария'
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('-created',)

    def __str__(self):
        return f'{self.text[:15]}'


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
    )
