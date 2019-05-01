# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
import requests

from hamcrest import (
    assert_that,
    calling,
    contains,
    empty,
    has_entries,
    has_properties,
    has_property,
    is_,
)
from xivo_test_helpers.auth import AuthClient as AuthMock
from xivo_test_helpers.hamcrest.raises import raises

from .helpers.base_dird import (
    BaseGooglePluginTestCase,
    BaseGoogleTestCase,
)

requests.packages.urllib3.disable_warnings()
VALID_TOKEN_MAIN_TENANT = 'valid-token-master-tenant'
MAIN_TENANT = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee10'
SUB_TENANT = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee11'


@pytest.mark.skip(reason='Not implemented')
class TestGooglePlugin(BaseGooglePluginTestCase):

    asset = 'plugin_dird_google'

    def config(self):
        return {
            'auth': {
                'host': 'localhost',
                'port': self.service_port(9497, 'auth-mock'),
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
            'type': 'google',
        }

    def test_plugin_lookup(self):
        self.auth_mock.set_external_auth(self.GOOGLE_EXTERNAL_AUTH)

        result = self.backend.search('war', self.LOOKUP_ARGS)

        assert_that(result, contains(has_entries(
            number='5555555555',
            email='wbros@wazoquebec.ongoogle.com',
            **self.WARIO
        )))

    def test_plugin_favorites(self):
        self.auth_mock.set_external_auth(self.GOOGLE_EXTERNAL_AUTH)

        result = self.backend.list(['an-id'], self.FAVORITE_ARGS)

        assert_that(result, contains(has_entries(
            number='5555555555',
            email='wbros@wazoquebec.ongoogle.com',
            **self.WARIO
        )))

    def test_plugin_reverse(self):
        self.auth_mock.set_external_auth(self.GOOGLE_EXTERNAL_AUTH)

        result = self.backend.first('5555555555', self.LOOKUP_ARGS)

        assert_that(result, has_entries(
            number='5555555555',
            email='wbros@wazoquebec.ongoogle.com',
            **self.WARIO
        ))


@pytest.mark.skip(reason='Not implemented')
class TestDirdGooglePlugin(BaseGoogleTestCase):

    asset = 'dird_google'

    BACKEND = 'google'
    display_body = {
        'name': 'default',
        'columns': [
            {'title': 'Firstname', 'field': 'firstname'},
            {'title': 'Lastname', 'field': 'lastname'},
            {'title': 'Number', 'field': 'number'},
        ],
    }

    def config(self):
        return {
            'auth': {
                'host': 'auth-mock',
                'port': 9497,
                'verify_certificate': False,
            },
            'first_matched_columns': [],
            'format_columns': {
                'phone': "{numbers[0]}",
                'phone_mobile': "{numbers_by_label[mobile]}",
                'reverse': '{name}',
            },
            'name': 'google',
            'searched_columns': [
                'name',
                "emails",
                "numbers",
            ],
            'type': 'google',
        }

    def setUp(self):
        super().setUp()
        self.auth_client_mock = AuthMock(host='0.0.0.0', port=self.service_port(9497, 'auth-mock'))

    def test_given_google_when_lookup_then_contacts_fetched(self):
        self.auth_client_mock.set_external_auth(self.GOOGLE_EXTERNAL_AUTH)

        result = self.client.directories.lookup(term='war', profile='default')
        assert_that(result, has_entries(
            results=contains(
                has_entries(column_values=contains('Wario')),
            )
        ))

    def test_given_no_google_when_lookup_then_no_result(self):
        self.auth_client_mock.reset_external_auth()

        result = self.client.directories.lookup(term='war', profile='default')
        result = result['results']

        assert_that(result, is_(empty()))

    def test_given_google_source_when_get_all_contacts_then_contacts_fetched(self):
        self.auth_client_mock.set_external_auth(self.GOOGLE_EXTERNAL_AUTH)

        result = self.client.backends.list_contacts_from_source(
            backend=self.BACKEND,
            source_uuid=self.source['uuid'],
        )

        assert_that(result, has_entries(
            total=1,
            filtered=1,
            items=contains(has_entries(
                name='Wario Bros',
                numbers=['5555555555'],
            )),
        ))

    def test_given_non_existing_google_source_when_get_all_contacts_then_not_found(self):
        self.auth_client_mock.set_external_auth(self.GOOGLE_EXTERNAL_AUTH)

        assert_that(
            calling(self.client.backends.list_contacts_from_source).with_args(
                backend=self.BACKEND,
                source_uuid='a-non-existing-source-uuid',
            ),
            raises(requests.HTTPError).matching(
                has_property('response', has_properties('status_code', 404))
            )
        )

    def test_given_google_source_and_non_existing_tenant_when_get_all_contacts_then_not_found(self):
        self.auth_client_mock.set_external_auth(self.GOOGLE_EXTERNAL_AUTH)

        assert_that(
            calling(self.client.backends.list_contacts_from_source).with_args(
                backend=self.BACKEND,
                source_uuid=self.source['uuid'],
                tenant_uuid=SUB_TENANT,
            ),
            raises(requests.HTTPError).matching(
                has_property('response', has_properties('status_code', 404))
            )
        )
