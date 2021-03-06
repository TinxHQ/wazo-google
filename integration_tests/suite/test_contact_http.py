# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from hamcrest import (
    assert_that,
    calling,
    contains,
    contains_inanyorder,
    has_entries,
)

from xivo_test_helpers.auth import AuthClient as AuthMock
from xivo_test_helpers.hamcrest.raises import raises

from .helpers.constants import (
    GOOGLE_CONTACT_LIST,
    HTTP_404,
    SUB_TENANT,
    UNKNOWN_UUID,
    VALID_TOKEN_MAIN_TENANT,
    VALID_TOKEN_SUB_TENANT,
)
from .helpers.base_dird import BaseGoogleAssetTestCase
from .helpers.fixtures import http as fixtures


class TestGoogleContactList(BaseGoogleAssetTestCase):

    asset = 'dird_google'

    def setUp(self):
        super().setUp()
        auth_port = self.service_port(9497, 'auth-mock')
        source = self.client.backends.create_source(
            'google',
            {
                'name': 'google',
                'auth': {'host': 'auth-mock', 'port': 9497, 'verify_certificate': False},
            },
        )
        self.source_uuid = source['uuid']

        auth_client_mock = AuthMock(host='localhost', port=auth_port)
        auth_client_mock.set_external_auth(self.GOOGLE_EXTERNAL_AUTH)

    def tearDown(self):
        self.client.backends.delete_source('google', self.source_uuid)
        super().tearDown()

    def test_unknown_source(self):
        assert_that(
            calling(self.list_).with_args(self.client, UNKNOWN_UUID),
            raises(Exception).matching(HTTP_404),
        )

    @fixtures.google_source(token=VALID_TOKEN_MAIN_TENANT)
    @fixtures.google_source(token=VALID_TOKEN_SUB_TENANT)
    def test_multi_tenant(self, sub, main):
        main_client = self.get_client(VALID_TOKEN_MAIN_TENANT)
        sub_client = self.get_client(VALID_TOKEN_SUB_TENANT)

        assert_that(
            calling(self.list_).with_args(sub_client, main['uuid']),
            raises(Exception).matching(HTTP_404),
        )

        assert_that(
            calling(self.list_).with_args(main_client, main['uuid'], tenant_uuid=SUB_TENANT),
            raises(Exception).matching(HTTP_404),
        )

    @fixtures.google_result(GOOGLE_CONTACT_LIST)
    def test_list(self, google_api):
        result = self.list_(self.client, self.source_uuid)
        assert_that(result, has_entries(
            items=contains_inanyorder(
                has_entries(
                    name='Mario Bros',
                    emails=contains_inanyorder(
                        'mario@bros.example.com',
                    ),
                    numbers=contains_inanyorder(
                        '+15555551111',
                        '+15555551234',
                    ),
                    numbers_by_label=has_entries(
                        home='+15555551111',
                        mobile='+15555551234',
                    ),
                ),
                has_entries(
                    name='Luigi Bros',
                    emails=contains_inanyorder(
                        'Luigi@bros.example.com',
                        'luigi_bros@caramail.com',
                    ),
                    numbers=contains_inanyorder(
                        '5555552222',
                        '+15555551111',
                        '+15555554567',
                    ),
                    numbers_by_label=has_entries(
                        'Mushroom land land-line', '5555552222',
                        'home', '+15555551111',
                        'mobile', '+15555554567',
                    ),
                ),
            ),
            total=2,
            filtered=2,
        ))

    @fixtures.google_result(GOOGLE_CONTACT_LIST)
    def test_pagination(self, google_api):
        mario = has_entries(name='Mario Bros')
        luigi = has_entries(name='Luigi Bros')

        assert_that(
            self.list_(self.client, self.source_uuid, order='name'),
            has_entries(items=contains(luigi, mario)),
        )

        assert_that(
            self.list_(self.client, self.source_uuid, order='name', direction='desc'),
            has_entries(items=contains(mario, luigi)),
        )

        assert_that(
            self.list_(self.client, self.source_uuid, order='name', limit=1),
            has_entries(items=contains(luigi)),
        )

        assert_that(
            self.list_(self.client, self.source_uuid, order='name', offset=1),
            has_entries(items=contains(mario)),
        )

    @fixtures.google_result(GOOGLE_CONTACT_LIST)
    def test_search(self, google_api):
        self.list_(self.client, self.source_uuid, search='mario'),
        google_api.verify(
            {
                'method': 'GET',
                'path': '/m8/feeds/contacts/default/full',
                'headers': {
                    'Authorization': ['Bearer an-access-token'],
                },
                'queryStringParameters': {
                    'q': ['mario'],
                },
            }
        )

    def list_(self, client, *args, **kwargs):
        return client.backends.list_contacts_from_source('google', *args, **kwargs)
