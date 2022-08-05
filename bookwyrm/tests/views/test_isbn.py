""" test for app action functionality """
import json
from unittest.mock import patch

from django.http import JsonResponse
from django.test import TestCase
from django.test.client import RequestFactory

from bookwyrm import models, views
from bookwyrm.tests.validate_html import validate_html
from bookwyrm.settings import DOMAIN


class IsbnViews(TestCase):
    """tag views"""

    def setUp(self):  # pylint: disable=invalid-name
        """we need basic test data and mocks"""
        self.factory = RequestFactory()
        with patch("bookwyrm.suggested_users.rerank_suggestions_task.delay"), patch(
            "bookwyrm.activitystreams.populate_stream_task.delay"
        ), patch("bookwyrm.lists_stream.populate_lists_task.delay"):
            self.local_user = models.User.objects.create_user(
                "mouse@local.com",
                "mouse@mouse.com",
                "mouseword",
                local=True,
                localname="mouse",
                remote_id="https://example.com/users/mouse",
            )
        self.work = models.Work.objects.create(title="Test Work")
        self.book = models.Edition.objects.create(
            title="Test Book",
            isbn_13="1234567890123",
            remote_id="https://example.com/book/1",
            parent_work=self.work,
        )
        models.SiteSettings.objects.create()

    def test_isbn_json_response(self):
        """searches local data only and returns book data in json format"""
        view = views.Isbn.as_view()
        request = self.factory.get("")
        with patch("bookwyrm.views.isbn.is_api_request") as is_api:
            is_api.return_value = True
            response = view(request, isbn="1234567890123")
        self.assertIsInstance(response, JsonResponse)

        data = json.loads(response.content)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "Test Book")
        self.assertEqual(data[0]["key"], f"https://{DOMAIN}/book/{self.book.id}")

    def test_isbn_html_response(self):
        """searches local data only and returns book data in json format"""
        view = views.Isbn.as_view()
        request = self.factory.get("")
        with patch("bookwyrm.views.isbn.is_api_request") as is_api:
            is_api.return_value = False
            response = view(request, isbn="1234567890123")
        self.assertEqual(response.status_code, 200)
        validate_html(response.render())
