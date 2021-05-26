import unittest
from json import loads
from reversewhois import Response, ErrorMessage


_json_response_ok = '''{
   "nextPageSearchAfter": null,
   "domainsCount": 2,
   "domainsList": [
        "airbnb.app",
        "airbnbhost.app"
    ]
}'''

_json_response_ok_with_dates = '''{
   "nextPageSearchAfter": null,
   "domainsCount": 2,
   "domainsList": [
        {
            "domainName": "airbnb.app",
            "audit": {
                "createdDate": "2021-01-10T18:52:41+00:00",
                "updatedDate": "2021-01-10T18:52:41+00:00"
            }
        },
        {
            "domainName": "airbnbhost.app",
            "audit": {
                "createdDate": "2021-01-10T18:52:41+00:00",
                "updatedDate": "2021-01-10T18:52:41+00:00"
            }
        }
    ]
}'''

_json_response_error = '''{
    "code": 403,
    "messages": "Access restricted. Check credits balance or enter the correct API key."
}'''


class TestModel(unittest.TestCase):

    def test_response_parsing(self):
        response = loads(_json_response_ok)
        parsed = Response(response)
        self.assertEqual(parsed.domains_count, response['domainsCount'])
        self.assertIsInstance(parsed.domains_list, list)
        self.assertEqual(
            parsed.domains_list[0].domain_name,
            response['domainsList'][0])

    def test_ok_with_dates(self):
        response = loads(_json_response_ok_with_dates)
        parsed = Response(response)
        self.assertEqual(parsed.domains_count, response['domainsCount'])
        self.assertIsInstance(parsed.domains_list, list)
        self.assertEqual(
            parsed.domains_list[1].domain_name,
            response['domainsList'][1]['domainName'])
        self.assertEqual(
            parsed.domains_list[1].audit_updated_date.strftime(
                "%Y-%m-%dT%H:%M:%S%z"),
            ''.join(response['domainsList'][1]['audit']['updatedDate']
                    .rsplit(':', 1))
        )
        self.assertEqual(
            parsed.domains_list[1].audit_created_date.strftime(
                "%Y-%m-%dT%H:%M:%S%z"),
            ''.join(response['domainsList'][1]['audit']['createdDate']
                    .rsplit(':', 1))
        )

    def test_error_parsing(self):
        error = loads(_json_response_error)
        parsed_error = ErrorMessage(error)
        self.assertEqual(parsed_error.code, error['code'])
        self.assertEqual(parsed_error.message, error['messages'])
