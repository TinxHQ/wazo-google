# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import json
import random
import string
import requests

from functools import wraps

from mockserver import MockServerClient as BaseMockServerClient

from ..constants import VALID_TOKEN_MAIN_TENANT


class UnVerifiedMockServerClient(BaseMockServerClient):

    def _put(self, endpoint, json=None):
        response = requests.put(
            self.url + endpoint,
            json=json,
            verify=False,
        )
        return response


def random_string(length=10):
    return ''.join(random.choice(string.ascii_lowercase) for _ in range(length))


def google_source(**source_args):
    def decorator(decorated):

        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            source_args.setdefault('name', random_string())
            source_args.setdefault('token', VALID_TOKEN_MAIN_TENANT)
            source_args.setdefault(
                'auth',
                {'host': 'auth', 'port': 9497, 'verify_certificate': False},
            )

            client = self.get_client(source_args['token'])
            source = client.backends.create_source(
                backend='google',
                body=source_args,
            )

            try:
                result = decorated(self, source, *args, **kwargs)
            finally:
                try:
                    self.client.backends.delete_source('google', source['uuid'])
                except Exception as e:
                    response = getattr(e, 'response', None)
                    status_code = getattr(response, 'status_code', None)
                    if status_code != 404:
                        raise
            return result
        return wrapper
    return decorator


def google_result(contact_list):
    def decorator(decorated):
        @wraps(decorated)
        def wrapper(self, *args, **kwargs):
            google_port = self.service_port(443, 'google.com')
            mock_server = UnVerifiedMockServerClient('https://localhost:{}'.format(google_port))
            expectation = mock_server.create_expectation(
                '/m8/feeds/contacts/default/full',
                contact_list,
                200,
            )
            expectation['times']['unlimited'] = True
            mock_server.mock_any_response(expectation)
            try:
                result = decorated(self, mock_server, *args, **kwargs)
            finally:
                mock_server.reset()
            return result
        return wrapper
    return decorator
