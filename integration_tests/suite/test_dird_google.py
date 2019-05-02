# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import requests

from hamcrest import (
    assert_that,
    contains,
    has_entries,
    has_item,
)

from xivo_test_helpers.auth import AuthClient as AuthMock

from .helpers.base_dird import BaseGoogleAssetTestCase
from .helpers.constants import GOOGLE_CONTACT_LIST
from .helpers.fixtures import http as fixtures

requests.packages.urllib3.disable_warnings()


class TestGooglePlugin(BaseGoogleAssetTestCase):

    asset = 'dird_google'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        client = cls.get_client()
        source_body = {
            'auth': {
                'host': 'auth-mock',
                'port': 9497,
                'verify_certificate': False,
            },
            'first_matched_columns': ['numbers'],
            'format_columns': {
                'phone_mobile': '{numbers_by_label[mobile]}',
                'phone': '{numbers[0]}',
                'email': '{emails[0]}',
                'reverse': '{name}',
            },
            'name': 'google',
            'searched_columns': [
                "name",
                "emails",
                "numbers",
            ],
        }
        display_body = {
            'name': 'default',
            'columns': [
                {'title': 'name', 'field': 'name'},
                {'title': 'email', 'field': 'email'},
                {'title': 'number', 'field': 'phone'},
                {'title': 'mobile', 'field': 'phone_mobile'},
            ],
        }
        display = client.displays.create(display_body)
        source = client.backends.create_source('google', source_body)

        profile_body = {
            'name': 'default',
            'display': display,
            'services': {
                'lookup': {'sources': [source]},
                'reverse': {'sources': [source]},
                'favorites': {'sources': [source]},
            },
        }
        profile = client.profiles.create(profile_body)

        cls.source_uuid = source['uuid']
        cls.display_uuid = display['uuid']
        cls.profile_uuid = profile['uuid']

        cls.auth_client_mock = AuthMock(host='0.0.0.0', port=cls.service_port(9497, 'auth-mock'))
        cls.auth_client_mock.set_external_auth(cls.GOOGLE_EXTERNAL_AUTH)

    @classmethod
    def tearDownClass(cls):
        client = cls.get_client()
        cls.auth_client_mock.reset_external_auth()
        client.backends.delete_source('google', cls.source_uuid)
        client.displays.delete(cls.display_uuid)
        client.profiles.delete(cls.profile_uuid)
        super().tearDownClass()

    @fixtures.google_result(GOOGLE_CONTACT_LIST)
    def test_plugin_lookup(self, google_api):
        result = self.client.directories.lookup(term='mario', profile='default')

        assert_that(result, has_entries(
            results=contains(
                has_entries(
                    backend='google',
                    source='google',
                    column_values=contains(
                        'Mario Bros',
                        'mario@bros.example.com',
                        '+15555551111',
                        '+15555551234',
                    ),
                ),
            ),
        ))

    @fixtures.google_result(GOOGLE_CONTACT_LIST)
    def test_plugin_favorites(self, google_api):
        response = self.client.directories.lookup(term='luigi', profile='default')
        luigi = response['results'][0]
        source = luigi['source']
        id_ = luigi['relations']['source_entry_id']

        self.client.directories.new_favorite(source, id_)

        result = self.client.directories.favorites(profile='default')
        assert_that(result, has_entries(
            results=contains(
                has_entries(column_values=has_item('Luigi Bros')),
            ),
        ))

    @fixtures.google_result(GOOGLE_CONTACT_LIST)
    def test_plugin_reverse(self, google_api):
        response = self.client.directories.reverse(
            exten='+15555551234',
            profile='default',
            xivo_user_uuid='uuid-tenant-master',
        )

        assert_that(response, has_entries(display='Mario Bros'))
