import copy
import datetime
import re

from .base import BaseModel
import sys

if sys.version_info < (3, 9):
    import typing


_re_date_format = re.compile(r'^\d\d\d\d-\d\d-\d\d$')
_re_datetime_format = re.compile(
    r'^(\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d)\+(\d\d):(\d\d)$')


def _datetime_value(values: dict, key: str) -> datetime.datetime or None:
    if key in values and values[key] is not None:
        value = values[key]
        match = _re_datetime_format.fullmatch(value)
        if match is not None:
            (dt, tz_hours, tz_minutes) = match.groups()
            value = "{}+{}{}".format(dt, tz_hours, tz_minutes)
            return datetime.datetime.strptime(
                value, '%Y-%m-%dT%H:%M:%S%z')

    return None


def _date_value(values: dict, key: str) -> datetime.date or None:
    if key in values and values[key] is not None:
        if _re_date_format.match(values[key]) is not None:
            return datetime.datetime.strptime(
                values[key], '%Y-%m-%d').date()

    return None


def _string_value(values: dict, key: str) -> str:
    if key in values and values[key]:
        return str(values[key])
    return ''


def _int_value(values: dict, key: str) -> int:
    if key in values and values[key]:
        return int(values[key])
    return 0


def _list_value(values: dict, key: str) -> list:
    if key in values and type(values[key]) is list:
        return copy.deepcopy(values[key])
    return []


def _list_of_objects(values: dict, key: str, classname: str) -> list:
    r = []
    if key in values and type(values[key]) is list:
        r = [globals()[classname](x) for x in values[key]]
    return r


def _timestamp2datetime(timestamp: int) -> datetime.datetime or None:
    if timestamp is not None:
        return datetime.datetime.fromtimestamp(timestamp)
    return None


class Domain(BaseModel):
    domain_name: str
    audit_created_date: datetime.datetime or None
    audit_updated_date: datetime.datetime or None

    def __init__(self, value):
        super().__init__()

        self.domain_name = ''
        self.audit_created_date = None
        self.audit_updated_date = None

        if type(value) is str:
            self.domain_name = value
        if type(value) is dict:
            self.domain_name = _string_value(value, 'domainName')
            if 'audit' in value:
                self.audit_created_date = _datetime_value(
                    value['audit'], 'createdDate')
                self.audit_updated_date = _datetime_value(
                    value['audit'], 'updatedDate')


class Response(BaseModel):
    domains_count: int
    next_page_search_after: str or None
    if sys.version_info < (3, 9):
        domains_list: typing.List[Domain]
    else:
        domains_list: [Domain]

    def __init__(self, values):
        super().__init__()

        self.domains_count = 0
        self.next_page_search_after = None
        self.domains_list = []

        if values is not None:
            self.domains_count = _int_value(values, 'domainsCount')
            self.next_page_search_after = _int_value(
                values, 'nextPageSearchAfter')
            self.domains_list = _list_of_objects(
                values, 'domainsList', 'Domain')

    def has_next(self) -> bool:
        """
        Checks if there are a next page
        """
        return self.next_page_search_after is not None \
            and self.next_page_search_after != 0


class ErrorMessage(BaseModel):
    code: int
    message: str

    def __init__(self, values):
        super().__init__()

        self.int = 0
        self.message = ''

        if values is not None:
            self.code = _int_value(values, 'code')
            self.message = _string_value(values, 'messages')
