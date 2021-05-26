import datetime
from json import loads, JSONDecodeError
import re

from .net.http import ApiRequester
from .models.response import Response
from .models.request import Fields
from .exceptions.error import ParameterError, EmptyApiKeyError, \
    UnparsableApiResponseError


class Client:
    __default_url = "https://reverse-whois.whoisxmlapi.com/api/v2"
    _api_requester: ApiRequester or None
    _api_key: str

    _re_api_key = re.compile(r'^at_[a-z0-9]{29}$', re.IGNORECASE)
    _SUPPORTED_FORMATS = ['json', 'xml']

    _PARSABLE_FORMAT = 'json'

    JSON_FORMAT = 'json'
    XML_FORMAT = 'xml'
    PREVIEW_MODE = 'preview'
    PURCHASE_MODE = 'purchase'
    CURRENT = 'current'
    HISTORIC = 'historic'

    __DATETIME_OR_NONE_MSG = 'Value should be None or an instance of ' \
                             'datetime.date'

    def __init__(self, api_key: str, **kwargs):
        """
        :param api_key: str: Your API key.
        :key base_url: str: (optional) API endpoint URL.
        :key timeout: float: (optional) API call timeout in seconds
        """

        self._api_key = ''

        self.api_key = api_key

        if 'base_url' not in kwargs:
            kwargs['base_url'] = Client.__default_url

        self.api_requester = ApiRequester(**kwargs)

    @property
    def api_key(self) -> str:
        return self._api_key

    @api_key.setter
    def api_key(self, value: str):
        self._api_key = Client._validate_api_key(value)

    @property
    def api_requester(self) -> ApiRequester or None:
        return self._api_requester

    @api_requester.setter
    def api_requester(self, value: ApiRequester):
        self._api_requester = value

    @property
    def base_url(self) -> str:
        return self._api_requester.base_url

    @base_url.setter
    def base_url(self, value: str or None):
        if value is None:
            self._api_requester.base_url = Client.__default_url
        else:
            self._api_requester.base_url = value

    @property
    def timeout(self) -> float:
        return self._api_requester.timeout

    @timeout.setter
    def timeout(self, value: float):
        self._api_requester.timeout = value

    def iterate_pages(self, **kwargs):
        """
        Iterate over all pages of domains related to given MX

        :key basic_terms: Required if advanced_terms aren't specified.
                Dictionary. Take a look at API documentation for the format
        :key advanced_terms: Required if basic_terms aren't specified
                List. Take a look at API documentation for the format
        :key search_type: Optional. Supported options - `Client.CURRENT`
                and `Client.HISTORIC`. Default is `Client.CURRENT`
        :key punycode: Optional. Boolean. Default value is `True`
        :key include_audit_dates: Optional. Boolean. Default value is `False`
        :key created_date_from: Optional. datetime.date.
        :key created_date_to: Optional. datetime.date.
        :key updated_date_from: Optional. datetime.date.
        :key updated_date_to: Optional. datetime.date.
        :key expires_date_from: Optional. datetime.date.
        :key expires_date_to: Optional. datetime.date.
        :key search_after: Optional. Integer.
        :yields Response: Instance of `Response` with a page.
        :raises ConnectionError:
        :raises ReverseWhoisApiError: Base class for all errors below
        :raises ResponseError: response contains an error message
        :raises ApiAuthError: Server returned 401, 402 or 403 HTTP code
        :raises BadRequestError: Server returned 400 or 422 HTTP code
        :raises HttpApiError: HTTP code >= 300 and not equal to above codes
        :raises ParameterError: invalid parameter's value
        """

        resp = self.purchase(**kwargs)
        yield resp
        while resp.has_next():
            resp = self.next_page(resp, **kwargs)
            yield resp

    def next_page(self, current_page: Response, **kwargs) \
            -> Response:
        """
        Get the next page if available, otherwise returns the given one

        :param Response current_page: The current page.
        :key basic_terms: Required if advanced_terms aren't specified.
                Dictionary. Take a look at API documentation for the format
        :key advanced_terms: Required if basic_terms aren't specified
                List. Take a look at API documentation for the format
        :key search_type: Optional. Supported options - `Client.CURRENT`
                and `Client.HISTORIC`. Default is `Client.CURRENT`
        :key punycode: Optional. Boolean. Default value is `True`
        :key include_audit_dates: Optional. Boolean. Default value is `False`
        :key created_date_from: Optional. datetime.date.
        :key created_date_to: Optional. datetime.date.
        :key updated_date_from: Optional. datetime.date.
        :key updated_date_to: Optional. datetime.date.
        :key expired_date_from: Optional. datetime.date.
        :key expired_date_to: Optional. datetime.date.
        :key search_after: Optional. Integer.
        :return: Instance of `Response` with a next page.
        :raises ConnectionError:
        :raises ReverseWhoisApiError: Base class for all errors below
        :raises ResponseError: response contains an error message
        :raises ApiAuthError: Server returned 401, 402 or 403 HTTP code
        :raises BadRequestError: Server returned 400 or 422 HTTP code
        :raises HttpApiError: HTTP code >= 300 and not equal to above codes
        :raises ParameterError: invalid parameter's value
        """

        if current_page.has_next():
            search_after = current_page.next_page_search_after
            kwargs['search_after'] = search_after
            return self.purchase(**kwargs)
        return current_page

    def preview(self, **kwargs) -> Response:
        """
        Get parsed API response as a `Response` instance.
        Mode = `preview`

        :key basic_terms: Required if advanced_terms aren't specified.
                Dictionary. Take a look at API documentation for the format
        :key advanced_terms: Required if basic_terms aren't specified
                List. Take a look at API documentation for the format
        :key search_type: Optional. Supported options - `Client.CURRENT`
                and `Client.HISTORIC`. Default is `Client.CURRENT`
        :key punycode: Optional. Boolean. Default value is `True`
        :key include_audit_dates: Optional. Boolean. Default value is `False`
        :key created_date_from: Optional. datetime.date.
        :key created_date_to: Optional. datetime.date.
        :key updated_date_from: Optional. datetime.date.
        :key updated_date_to: Optional. datetime.date.
        :key expired_date_from: Optional. datetime.date.
        :key expired_date_to: Optional. datetime.date.
        :key search_after: Optional. Integer.
        :return: `Response` instance
        :raises ConnectionError:
        :raises ReverseWhoisApiError: Base class for all errors below
        :raises ResponseError: response contains an error message
        :raises ApiAuthError: Server returned 401, 402 or 403 HTTP code
        :raises BadRequestError: Server returned 400 or 422 HTTP code
        :raises HttpApiError: HTTP code >= 300 and not equal to above codes
        :raises ParameterError: invalid parameter's value
        """
        kwargs['mode'] = Client.PREVIEW_MODE
        return self.data(**kwargs)

    def purchase(self, **kwargs):
        """
        Get parsed API response as a `Response` instance.
        Mode = `purchase`

        :key basic_terms: Required if advanced_terms aren't specified.
                Dictionary. Take a look at API documentation for the format
        :key advanced_terms: Required if basic_terms aren't specified
                List. Take a look at API documentation for the format
        :key search_type: Optional. Supported options - `Client.CURRENT`
                and `Client.HISTORIC`. Default is `Client.CURRENT`
        :key punycode: Optional. Boolean. Default value is `True`
        :key include_audit_dates: Optional. Boolean. Default value is `False`
        :key created_date_from: Optional. datetime.date.
        :key created_date_to: Optional. datetime.date.
        :key updated_date_from: Optional. datetime.date.
        :key updated_date_to: Optional. datetime.date.
        :key expired_date_from: Optional. datetime.date.
        :key expired_date_to: Optional. datetime.date.
        :key search_after: Optional. Integer.
        :return: `Response` instance
        :raises ConnectionError:
        :raises ReverseWhoisApiError: Base class for all errors below
        :raises ResponseError: response contains an error message
        :raises ApiAuthError: Server returned 401, 402 or 403 HTTP code
        :raises BadRequestError: Server returned 400 or 422 HTTP code
        :raises HttpApiError: HTTP code >= 300 and not equal to above codes
        :raises ParameterError: invalid parameter's value
        """
        kwargs['mode'] = Client.PURCHASE_MODE
        return self.data(**kwargs)

    def data(self, **kwargs) -> Response:
        """
        Get parsed API response as a `Response` instance.

        :key basic_terms: Required if advanced_terms aren't specified.
                Dictionary. Take a look at API documentation for the format
        :key advanced_terms: Required if basic_terms aren't specified
                List. Take a look at API documentation for the format
        :key mode: Optional. Supported options - `Client.PREVIEW_MODE` and
                `Client.PURCHASE_MODE`. Default is `Client.PREVIEW_MODE`
        :key search_type: Optional. Supported options - `Client.CURRENT`
                and `Client.HISTORIC`. Default is `Client.CURRENT`
        :key punycode: Optional. Boolean. Default value is `True`
        :key include_audit_dates: Optional. Boolean. Default value is `False`
        :key created_date_from: Optional. datetime.date.
        :key created_date_to: Optional. datetime.date.
        :key updated_date_from: Optional. datetime.date.
        :key updated_date_to: Optional. datetime.date.
        :key expired_date_from: Optional. datetime.date.
        :key expired_date_to: Optional. datetime.date.
        :key search_after: Optional. Integer.
        :return: `Response` instance
        :raises ConnectionError:
        :raises ReverseWhoisApiError: Base class for all errors below
        :raises ResponseError: response contains an error message
        :raises ApiAuthError: Server returned 401, 402 or 403 HTTP code
        :raises BadRequestError: Server returned 400 or 422 HTTP code
        :raises HttpApiError: HTTP code >= 300 and not equal to above codes
        :raises ParameterError: invalid parameter's value
        """

        kwargs['response_format'] = Client._PARSABLE_FORMAT

        response = self.raw_data(**kwargs)
        try:
            parsed = loads(str(response))
            if 'domainsCount' in parsed:
                return Response(parsed)
            raise UnparsableApiResponseError(
                "Could not find the correct root element.", None)
        except JSONDecodeError as error:
            raise UnparsableApiResponseError("Could not parse API response", error)

    def raw_data(self, **kwargs) -> str:
        """
        Get raw API response.

        :key basic_terms: Required if advanced_terms aren't specified.
                Dictionary. Take a look at API documentation for the format
        :key advanced_terms: Required if basic_terms aren't specified
                List. Take a look at API documentation for the format
        :key mode: Optional. Supported options - `Client.PREVIEW_MODE` and
                `Client.PURCHASE_MODE`. Default is `Client.PREVIEW_MODE`
        :key search_type: Optional. Supported options - `Client.CURRENT`
                and `Client.HISTORIC`. Default is `Client.CURRENT`
        :key punycode: Optional. Boolean. Default value is `True`
        :key include_audit_dates: Optional. Boolean. Default value is `False`
        :key created_date_from: Optional. datetime.date.
        :key created_date_to: Optional. datetime.date.
        :key updated_date_from: Optional. datetime.date.
        :key updated_date_to: Optional. datetime.date.
        :key expired_date_from: Optional. datetime.date.
        :key expired_date_to: Optional. datetime.date.
        :key response_format: Optional. use constants
                JSON_FORMAT and XML_FORMAT
        :key search_after: Optional. Integer.
        :return: str
        :raises ConnectionError:
        :raises ReverseWhoisApiError: Base class for all errors below
        :raises ResponseError: response contains an error message
        :raises ApiAuthError: Server returned 401, 402 or 403 HTTP code
        :raises BadRequestError: Server returned 400 or 422 HTTP code
        :raises HttpApiError: HTTP code >= 300 and not equal to above codes
        :raises ParameterError: invalid parameter's value
        """

        if self.api_key == '':
            raise EmptyApiKeyError('')

        if 'basic_terms' in kwargs:
            basic_terms = Client._validate_basic_terms(kwargs['basic_terms'])
        else:
            basic_terms = None

        if 'advanced_terms' in kwargs:
            advanced_terms = Client._validate_advanced_terms(
                kwargs['advanced_terms'])
        else:
            advanced_terms = None

        if not advanced_terms and not basic_terms:
            raise ParameterError(
                "Required one from basic_terms and advanced_terms")

        if 'output_format' in kwargs:
            kwargs['response_format'] = kwargs['output_format']
        if 'response_format' in kwargs:
            response_format = Client._validate_response_format(
                kwargs['response_format'])
        else:
            response_format = Client._PARSABLE_FORMAT

        if 'search_type' in kwargs:
            search_type = Client._validate_search_type(kwargs['search_type'])
        else:
            search_type = Client.CURRENT

        if 'search_after' in kwargs:
            search_after = Client._validate_search_after(
                kwargs['search_after'])
        else:
            search_after = None

        if 'punycode' in kwargs:
            punycode = Client._validate_punycode(kwargs['punycode'])
        else:
            punycode = True

        if 'include_audit_dates' in kwargs:
            include_audit_dates = Client._validate_include_audit_dates(
                kwargs['include_audit_dates'])
        else:
            include_audit_dates = False

        if 'mode' in kwargs:
            mode = Client._validate_mode(kwargs['mode'])
        else:
            mode = Client.PREVIEW_MODE

        if 'created_date_from' in kwargs:
            created_date_from = Client._validate_date(
                kwargs['created_date_from']
            )
        else:
            created_date_from = None

        if 'created_date_to' in kwargs:
            created_date_to = Client._validate_date(
                kwargs['created_date_to']
            )
        else:
            created_date_to = None

        if 'updated_date_from' in kwargs:
            updated_date_from = Client._validate_date(
                kwargs['updated_date_from']
            )
        else:
            updated_date_from = None

        if 'updated_date_to' in kwargs:
            updated_date_to = Client._validate_date(
                kwargs['updated_date_to']
            )
        else:
            updated_date_to = None

        if 'expired_date_from' in kwargs:
            expired_date_from = Client._validate_date(
                kwargs['expired_date_from']
            )
        else:
            expired_date_from = None

        if 'expired_date_to' in kwargs:
            expired_date_to = Client._validate_date(
                kwargs['expired_date_to']
            )
        else:
            expired_date_to = None

        return self._api_requester.post(self._build_payload(
            self.api_key,
            basic_terms,
            advanced_terms,
            mode,
            punycode,
            search_type,
            search_after,
            include_audit_dates,
            response_format,
            created_date_from,
            created_date_to,
            updated_date_from,
            updated_date_to,
            expired_date_from,
            expired_date_to,
        ))

    @staticmethod
    def _validate_api_key(api_key) -> str:
        if Client._re_api_key.search(
                str(api_key)
        ) is not None:
            return str(api_key)
        else:
            raise ParameterError("Invalid API key format.")

    @staticmethod
    def _validate_basic_terms(value) -> dict:
        include, exclude = [], []
        if value is None:
            raise ParameterError("Terms list cannot be None.")
        elif type(value) is dict:
            if 'include' in value:
                include = list(map(lambda s: str(s), value['include']))
                include = list(
                    filter(lambda s: s is not None and len(s) > 0, include))
                if 4 <= len(include) <= 1:
                    raise ParameterError("Include terms list must include "
                                         "from 1 to 4 terms.")
            if 'exclude' in value:
                exclude = list(map(lambda s: str(s), value['exclude']))
                exclude = list(
                    filter(lambda s: s is not None and len(s) > 0, exclude))
                if 4 <= len(exclude) <= 0:
                    raise ParameterError("Exclude terms list must include "
                                         "from 0 to 4 terms.")
            if include:
                return {'include': include, 'exclude': exclude}

        raise ParameterError("Expected a dict with 2 lists of strings.")

    @staticmethod
    def _validate_advanced_terms(value) -> list:
        if value is None:
            raise ParameterError("Terms list cannot be None.")
        elif type(value) is list:
            if 4 <= len(value) < 1:
                raise ParameterError(
                    "Terms list must include form 1 to 4 items.")
            for item in value:
                if 'field' not in item or 'term' not in item:
                    raise ParameterError(
                        "Invalid advanced search terms format.")
                if item['field'] not in Fields.values():
                    raise ParameterError("Unknown field name.")
                if item['term'] is None or type(item['term']) is not str \
                        or len(item['term']) < 2:
                    raise ParameterError("Term should be non-empty string.")
            return value

        raise ParameterError("Expected a list of pairs field <-> term.")

    @staticmethod
    def _validate_search_after(value):
        if value is not None and int(value) > 0:
            return int(value)

        raise ParameterError(
            "Search after parameter value must be an integer greater "
            "than zero or None")

    @staticmethod
    def _validate_response_format(value: str):
        if value.lower() in [Client.JSON_FORMAT, Client.XML_FORMAT]:
            return value.lower()

        raise ParameterError(
            f"Response format must be {Client.JSON_FORMAT} "
            f"or {Client.XML_FORMAT}")

    @staticmethod
    def _validate_include_audit_dates(value: bool):
        if value in [True, False]:
            return value

        raise ParameterError("Value must be True or False")

    @staticmethod
    def _validate_mode(value: str):
        if value.lower() in [Client.PREVIEW_MODE, Client.PURCHASE_MODE]:
            return value.lower()

        raise ParameterError(
            f"Mode must be {Client.PREVIEW_MODE} or {Client.PURCHASE_MODE}")

    @staticmethod
    def _validate_punycode(value: bool):
        if value in [True, False]:
            return value

        raise ParameterError(
            "Punycode parameter value must be True or False")

    @staticmethod
    def _validate_search_type(value: str):
        if value.lower() in [Client.CURRENT, Client.HISTORIC]:
            return value.lower()

        raise ParameterError(
            f"Search type must be {Client.CURRENT} or {Client.HISTORIC}")

    @staticmethod
    def _validate_date(value: datetime.date or None):
        if value is None or isinstance(value, datetime.date):
            return str(value)

        raise ParameterError(Client.__DATETIME_OR_NONE_MSG)

    @staticmethod
    def _build_payload(
            api_key,
            basic_terms,
            advanced_terms,
            mode,
            punycode,
            search_type,
            search_after,
            include_audit_dates,
            response_format,
            created_date_from,
            created_date_to,
            updated_date_from,
            updated_date_to,
            expired_date_from,
            expired_date_to,
    ) -> dict:
        tmp = {
            'apiKey': api_key,
            'mode': mode,
            'punycode': punycode,
            'searchType': search_type,
            'includeAuditDates': include_audit_dates,
            'responseFormat': response_format,
            'createdDateFrom': created_date_from,
            'createdDateTo': created_date_to,
            'updatedDateFrom': updated_date_from,
            'updatedDateTo': updated_date_to,
            'expiredDateFrom': expired_date_from,
            'expiredDateTo': expired_date_to,
            'searchAfter': search_after,
            'basicSearchTerms': basic_terms,
            'advancedSearchTerms': advanced_terms
        }

        payload = {}
        for k, v in tmp.items():
            if v is not None:
                payload[k] = v
        return payload
