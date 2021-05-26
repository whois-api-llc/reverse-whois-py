.. image:: https://img.shields.io/badge/License-MIT-green.svg
    :alt: reverse-whois-py license
    :target: https://opensource.org/licenses/MIT

.. image:: https://img.shields.io/pypi/v/reverse-whois.svg
    :alt: reverse-whois-py release
    :target: https://pypi.org/project/reverse-whois

.. image:: https://github.com/whois-api-llc/reverse-whois-py/workflows/Build/badge.svg
    :alt: reverse-whois-py build
    :target: https://github.com/whois-api-llc/reverse-whois-py/actions

========
Overview
========

The client library for
`Reverse Whois API <https://reverse-whois.whoisxmlapi.com/>`_
in Python language.

The minimum Python version is 3.6.

Installation
============

.. code-block:: shell

    pip install reverse-whois

Examples
========

Full API documentation available `here <https://reverse-whois.whoisxmlapi.com/api/documentation/making-requests>`_

Create a new client
-------------------

.. code-block:: python

    from reversewhois import *

    client = Client('Your API key')

Make basic requests
-------------------

.. code-block:: python

    # Get the number of domains.
    terms = {
        'include': ['blog']
    }
    result = client.preview(basic_terms=terms)
    print(result.domains_count)

    # Get raw API response
    raw_result = client.raw_data(
        basic_terms=terms,
        response_format=Client.XML_FORMAT,
        mode=Client.PREVIEW_MODE)

    # Get list of registered/dropped domains (up to 10,000)
    result = client.purchase(
        basic_terms=terms
    )

Advanced usage
-------------------

Extra request parameters

.. code-block:: python

    advanced_terms = [{
        'field': Fields.domain_name,
        'term': "whoisxmlapi.*"
    }]
    updated_date = datetime.date(2020, 1, 1)
    result = client.purchase(
        advanced_terms=advanced_terms,
        updated_date_from=updated_date,
        include_audit_dates=True,
        punycode=False)

    #Next page
    response = client.purchase(
        basic_terms=terms
    )
    if response.has_next():
        next_page = client.next_page(
            current_page=response,
            basic_terms=terms
        )

    #Iterating
    for page in client.iterate_pages(basic_terms=terms):
        print(page)