from http import HTTPStatus

from django.test import Client, TestCase
from django.urls import reverse


class PostModelTest(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_url_templates_about(self):
        url_templates_about = {
            '/about/author/': 'about/author.html',
            '/about/tech/': 'about/tech.html',
        }
        for url, templates in url_templates_about.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, templates)

    def test_about_pages_accessible_by_name(self):
        space_name = {
            reverse('about:author'): 'about/author.html',
            reverse('about:tech'): 'about/tech.html',
        }
        for url, template in space_name.items():
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)
                self.assertTemplateUsed(response, template)
