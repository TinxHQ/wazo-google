# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
import requests

from hamcrest import (
    assert_that,
    calling,
    contains,
    empty,
    equal_to,
    has_entries,
    has_entry,
    has_item,
    has_properties,
    has_property,
    is_,
    not_,
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
            'endpoint': 'http://localhost:{}/me/contacts'.format(self.service_port(80, 'google-mock')),
            'first_matched_columns': ['businessPhones', 'mobilePhone'],
            'format_columns': {
                'number': '{businessPhones[0]}',
                'email': '{emailAddresses[0][address]}',
            },
            'name': 'google',
            'searched_columns': [
                "givenName",
                "surname",
                "businessPhones"
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
class TestGooglePluginWrongEndpoint(BaseGooglePluginTestCase):

    asset = 'plugin_dird_google'

    def config(self):
        return {
            'auth': {
                'host': 'localhost',
                'port': self.service_port(9497, 'auth-mock'),
                'verify_certificate': False,
            },
            'endpoint': 'wrong-endpoint',
            'first_matched_columns': [],
            'format_columns': {
                'display_name': "{firstname} {lastname}",
                'name': "{firstname} {lastname}",
                'reverse': "{firstname} {lastname}",
                'phone_mobile': "{mobile}",
            },
            'name': 'google',
            'searched_columns': [],
            'type': 'google',
        }

    def test_plugin_lookup_with_wrong_endpoint(self):
        self.auth_mock.set_external_auth(self.GOOGLE_EXTERNAL_AUTH)

        result = self.backend.search('war', self.LOOKUP_ARGS)

        assert_that(result, is_(empty()))


@pytest.mark.skip(reason='Not implemented')
class TestDirdClientGooglePlugin(BaseGoogleTestCase):

    asset = 'dird_google'
    BACKEND = 'google'

    def config(self):
        return {
            'auth': {
                'host': 'auth-mock',
                'port': 9497,
                'verify_certificate': False,
            },
            'endpoint': 'http://google-mock:80/me/contacts',
            'first_matched_columns': ['mobilePhone'],
            'format_columns': {
                'display_name': "{displayName}",
                'name': "{displayName}",
                'reverse': "{displayName}",
                'phone_mobile': "{mobilePhone}",
            },
            'name': 'google',
            'searched_columns': [],
            'type': 'google',
        }

    def setUp(self):
        super().setUp()
        self.client.backends.delete_source(backend=self.BACKEND, source_uuid=self.source['uuid'])

    def tearDown(self):
        try:
            response = self.client.backends.list_sources(backend=self.BACKEND)
            sources = response['items']
            for source in sources:
                self.client.backends.delete_source(backend=self.BACKEND, source_uuid=source['uuid'])
        except requests.HTTPError:
            pass

        super().tearDown()

    def test_when_create_source_then_no_error(self):
        assert_that(
            calling(self.client.backends.create_source).with_args(
                backend=self.BACKEND,
                body=self.config(),
            ),
            not_(raises(requests.HTTPError))
        )

    def test_given_source_when_delete_then_ok(self):
        source = self.client.backends.create_source(backend=self.BACKEND, body=self.config())

        assert_that(
            calling(self.client.backends.delete_source).with_args(
                backend=self.BACKEND,
                source_uuid=source['uuid'],
            ),
            not_(raises(requests.HTTPError))
        )

    def test_when_delete_then_raises(self):
        assert_that(
            calling(self.client.backends.delete_source).with_args(
                backend=self.BACKEND,
                source_uuid='a-non-existing-source-uuid',
            ),
            raises(requests.HTTPError).matching(
                has_property('response', has_properties('status_code', 404))
            )
        )

    def test_given_source_when_get_then_ok(self):
        config = self.config()

        created = self.client.backends.create_source(backend=self.BACKEND, body=config)

        source = self.client.backends.get_source(backend=self.BACKEND, source_uuid=created['uuid'])
        assert_that(source, has_entries(
            uuid=created['uuid'],
            auth=config['auth'],
            format_columns=config['format_columns'],
            first_matched_columns=config['first_matched_columns'],
        ))

    def test_given_source_when_edit_then_ok(self):
        source = self.client.backends.create_source(backend=self.BACKEND, body=self.config())
        source.update({'name': 'a-new-name'})

        assert_that(
            calling(self.client.backends.edit_source).with_args(
                backend=self.BACKEND,
                source_uuid=source['uuid'],
                body=source,
            ),
            not_(raises(requests.HTTPError))
        )

    def test_given_source_when_list_sources_then_ok(self):
        source = self.client.backends.create_source(backend=self.BACKEND, body=self.config())

        sources = self.client.backends.list_sources(backend=self.BACKEND)

        assert_that(next(iter(sources['items'])), has_entry('uuid', source['uuid']))

    def test_given_source_when_list_then_ok(self):
        self.client.backends.create_source(backend=self.BACKEND, body=self.config())

        backends = self.client.backends.list()

        assert_that(backends['items'], has_item({'name': self.BACKEND}))

    def test_given_source_and_google_when_list_contacts_then_contacts_listed(self):
        source = self.client.backends.create_source(backend=self.BACKEND, body=self.config())
        auth_client_mock = AuthMock(host='0.0.0.0', port=self.service_port(9497, 'auth-mock'))
        auth_client_mock.set_external_auth(self.GOOGLE_EXTERNAL_AUTH)

        result = self.client.backends.list_contacts_from_source(backend=self.BACKEND, source_uuid=source['uuid'])
        assert_that(result, has_entries(
            items=has_item(
                has_entries(givenName='Wario'),
            ),
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
            'endpoint': 'http://google-mock:80/me/contacts',
            'first_matched_columns': [],
            'format_columns': {
                'firstname': "{givenName}",
                'lastname': "{surname}",
                'number': "{businessPhones[0]}",
            },
            'name': 'google',
            'searched_columns': [
                "givenName",
                "surname",
                "businessPhones"
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
                displayName='Wario Bros',
                surname='Bros',
                businessPhones=['5555555555'],
                givenName='Wario',
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


@pytest.mark.skip(reason='Not implemented')
class TestDirdGooglePluginNoEndpoint(BaseGoogleTestCase):

    asset = 'dird_google'

    BACKEND = 'google'

    def config(self):
        return {
            'auth': {
                'host': 'auth-mock',
                'port': 9497,
                'verify_certificate': False,
            },
            'first_matched_columns': [],
            'format_columns': {
                'firstname': "{givenName}",
                'lastname': "{surname}",
                'reverse': "{displayName}",
                'phone_mobile': "{mobilePhone}",
            },
            'name': 'google',
            'searched_columns': [
                "givenName",
                "surname",
                "businessPhones"
            ],
            'type': 'google',
        }

    def test_given_google_when_lookup_with_no_endpoint_then_no_error(self):
        assert_that(self.source['endpoint'], is_(equal_to('https://people.googleapis.com/$discovery/rest')))
        assert_that(
            calling(self.client.directories.lookup).with_args(term='war', profile='default'),
            not_(raises(Exception))
        )


@pytest.mark.skip(reason='Not implemented')
class TestDirdGooglePluginErrorEndpoint(BaseGoogleTestCase):

    asset = 'dird_google'

    BACKEND = 'google'

    def config(self):
        return {
            'auth': {
                'host': 'auth-mock',
                'port': 9497,
                'verify_certificate': False,
            },
            'endpoint': 'http://google-mock:80/me/contacts/error',
            'first_matched_columns': [],
            'format_columns': {
                'display_name': "{firstname} {lastname}",
                'name': "{firstname} {lastname}",
                'reverse': "{firstname} {lastname}",
                'phone_mobile': "{mobile}",
            },
            'name': 'google',
            'searched_columns': [],
            'type': 'google',
        }

    def test_given_google_when_lookup_with_error_endpoint_then_no_error(self):
        assert_that(
            calling(self.client.directories.lookup).with_args(
                term='war',
                profile='default',
            ),
            not_(raises(Exception))
        )

    def test_given_google_when_fetch_all_contacts_with_error_endpoint(self):
        assert_that(
            calling(self.client.backends.list_contacts_from_source).with_args(
                backend=self.BACKEND,
                source_uuid=self.source['uuid']
            ),
            raises(requests.HTTPError).matching(
                has_property('response', has_properties('status_code', 503))
            )
        )
