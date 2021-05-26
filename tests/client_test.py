import datetime
import os
import unittest
from reversewhois import Client, Fields
from reversewhois import ParameterError, ApiAuthError


class TestClient(unittest.TestCase):
    """
    Final integration tests without mocks.

    Active API_KEY is required.
    """
    def setUp(self) -> None:
        self.client = Client(os.getenv('API_KEY'))
        self.correct_basic_terms = {
            'include': ['medicine', 'google'],
            'exclude': ['blog']
        }
        self.correct_advanced_terms = [
            {
                'field': Fields.domain_name,
                'term': "facebook.*"
            }
        ]

        self.incorrect_basic_terms = {
            'include': []
        }

        self.incorrect_advanced_terms = [
            {
                'field': 'abrakadabra'
            }
        ]

    def test_get_correct_data(self):
        response = self.client.data(
            basic_terms=self.correct_basic_terms,
            mode=Client.PURCHASE_MODE,
            include_audit_dates=True
        )
        self.assertIsNotNone(response.domains_count)

    def test_extra_parameters(self):
        response = self.client.data(
            basic_terms=self.correct_basic_terms,
            mode=Client.PREVIEW_MODE,
            search_type=Client.HISTORIC,
            created_date_from=datetime.date(year=2019, month=1, day=1)
        )
        self.assertIsNotNone(response.domains_count)

    def test_empty_terms(self):
        with self.assertRaises(ParameterError):
            self.client.data()

    def test_getting_next_page(self):
        basic = {
            'include': ['medicine']
        }
        resp = self.client.data(
            basic_terms=basic,
            mode=Client.PURCHASE_MODE
        )
        if resp.has_next():
            next_page = self.client.next_page(
                current_page=resp,
                basic_terms=basic,
                mode=Client.PURCHASE_MODE)
            self.assertGreater(len(next_page.domains_list), 0)

    def test_iterating(self):
        limit = 3
        basic = {
            'include': ['medicine']
        }
        for page in self.client.iterate_pages(
            basic_terms=basic,
            mode=Client.PURCHASE_MODE
        ):
            self.assertIsNotNone(page.domains_count)
            limit -= 1
            if limit <= 0:
                break

    def test_incorrect_api_key(self):
        client = Client('at_00000000000000000000000000000')
        with self.assertRaises(ApiAuthError):
            client.data(basic_terms=self.correct_basic_terms)

    def test_raw_data(self):
        response = self.client.raw_data(
            basic_terms=self.correct_basic_terms,
            response_format=Client.XML_FORMAT)
        self.assertTrue(response.startswith('<?xml'))

    def test_advanced(self):
        response = self.client.data(
            advanced_terms=self.correct_advanced_terms
        )
        self.assertIsNotNone(response.domains_count)

    def test_incorrect_basic(self):
        with self.assertRaises(ParameterError):
            self.client.data(basic_terms=self.incorrect_basic_terms)

    def test_incorrect_advanced(self):
        with self.assertRaises(ParameterError):
            self.client.data(advanced_terms=self.incorrect_advanced_terms)

    def test_preview(self):
        response = self.client.preview(basic_terms=self.correct_basic_terms)
        self.assertGreater(response.domains_count, 0)

    def test_purchase(self):
        response = self.client.purchase(basic_terms=self.correct_basic_terms)
        self.assertGreater(len(response.domains_list), 0)


if __name__ == '__main__':
    unittest.main()
