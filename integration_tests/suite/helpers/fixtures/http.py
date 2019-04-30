# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import random
import string

from functools import wraps

from ..constants import VALID_TOKEN_MAIN_TENANT


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
