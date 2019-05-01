# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import os
import logging
import requests

from stevedore import DriverManager
from mock import Mock

from wazo_dird_client import Client as DirdClient
from xivo_test_helpers.asset_launching_test_case import AssetLaunchingTestCase
from xivo_test_helpers.auth import AuthClient as AuthMock


logger = logging.getLogger(__name__)

ASSET_ROOT = os.path.join(os.path.dirname(__file__), '../..', 'assets')
VALID_TOKEN_MAIN_TENANT = 'valid-token-master-tenant'


class BackendWrapper:

    def __init__(self, backend, dependencies):
        manager = DriverManager(
            namespace='wazo_dird.backends',
            name=backend,
            invoke_on_load=True,
        )
        self._source = manager.driver
        self._source.load(dependencies)

    def unload(self):
        self._source.unload()

    def search(self, term, profile):
        return [r.fields for r in self.search_raw(term, profile)]

    def search_raw(self, term, profile):
        return self._source.search(term, profile)

    def first(self, term, *args, **kwargs):
        return self._source.first_match(term, *args, **kwargs).fields

    def list(self, source_ids, *args, **kwargs):
        results = self._source.list(source_ids, *args, **kwargs)
        return [r.fields for r in results]


class BaseGoogleAssetTestCase(AssetLaunchingTestCase):

    assets_root = ASSET_ROOT
    service = 'dird'

    GOOGLE_EXTERNAL_AUTH = {
        "access_token": "an-access-token",
        "scope": "a-scope",
        "token_expiration": 42
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.host = 'localhost'
        cls.port = cls.service_port(9489, 'dird')

    @property
    def client(self):
        return self.get_client()

    def get_client(self, token=VALID_TOKEN_MAIN_TENANT):
        return DirdClient(self.host, self.port, token=token, verify_certificate=False)


class BaseGoogleTestCase(BaseGoogleAssetTestCase):

    LOOKUP_ARGS = {
        'xivo_user_uuid': 'a-xivo-uuid',
        'token': 'a-token',
    }
    FAVORITE_ARGS = {
        'xivo_user_uuid': 'a-xivo-uuid',
        'token': 'a-token',
    }

    WARIO = {
        'name': 'Wario Bros',
        'numbers_by_label': {},
    }

    def setUp(self):
        super().setUp()
        self.source = self.client.backends.create_source(
            backend=self.BACKEND,
            body=self.config(),
        )
        self.display = self.client.displays.create({
            'name': 'display',
            'columns': [
                {'field': 'firstname'},
            ],
        })
        self.profile = self.client.profiles.create({
            'name': 'default',
            'display': self.display,
            'services': {'lookup': {'sources': [self.source]}},
        })
        self.auth_client_mock = AuthMock(host='0.0.0.0', port=self.service_port(9497, 'auth-mock'))
        self.auth_client_mock.set_external_auth(self.GOOGLE_EXTERNAL_AUTH)

    def tearDown(self):
        try:
            self.client.profiles.delete(self.profile['uuid'])
            self.client.displays.delete(self.display['uuid'])
            self.client.backends.delete_source(
                backend=self.BACKEND,
                source_uuid=self.source['uuid'],
            )
        except requests.HTTPError:
            pass

        self.auth_client_mock.reset_external_auth()
        super().tearDown()


class BaseGooglePluginTestCase(BaseGoogleTestCase):

    asset = 'plugin_dird_google'

    def setUp(self):
        self.auth_mock = AuthMock(host='0.0.0.0', port=self.service_port(9497, 'auth-mock'))
        self.backend = BackendWrapper(
            'google',
            {
                'config': self.config(),
                'api': Mock()
            }
        )

    def tearDown(self):
        self.backend.unload()
        self.auth_mock.reset_external_auth()
