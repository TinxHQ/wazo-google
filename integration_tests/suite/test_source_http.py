# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from contextlib import contextmanager
import requests

from hamcrest import (
    assert_that,
    calling,
    contains,
    contains_inanyorder,
    equal_to,
    has_entries,
    has_properties,
    not_,
)
from mock import ANY
from xivo_test_helpers.hamcrest.uuid_ import uuid_
from xivo_test_helpers.hamcrest.raises import raises

from .helpers.base_dird import (
    BaseGoogleAssetTestCase,
    BaseGoogleTestCase,
)
from .helpers.constants import (
    UNKNOWN_UUID,
    VALID_TOKEN_MAIN_TENANT,
    VALID_TOKEN_SUB_TENANT,
    MAIN_TENANT,
    SUB_TENANT,
)
from .helpers.fixtures import http as fixtures

HTTP_401 = has_properties(response=has_properties(status_code=401))
HTTP_404 = has_properties(response=has_properties(status_code=404))
HTTP_409 = has_properties(response=has_properties(status_code=409))


class BaseGoogleCRUDTestCase(BaseGoogleAssetTestCase):

    asset = 'dird_google'


class TestDelete(BaseGoogleCRUDTestCase):

    @fixtures.google_source()
    def test_delete(self, source):
        assert_that(
            calling(self.client.backends.delete_source).with_args('google', source['uuid']),
            not_(raises(Exception)),
        )
        assert_that(
            calling(self.client.backends.get_source).with_args('google', source['uuid']),
            raises(Exception).matching(HTTP_404)
        )

    def test_delete_unknown(self):
        assert_that(
            calling(self.client.backends.delete_source).with_args('google', UNKNOWN_UUID),
            raises(Exception).matching(HTTP_404)
        )

    @fixtures.google_source(token=VALID_TOKEN_MAIN_TENANT)
    @fixtures.google_source(token=VALID_TOKEN_SUB_TENANT)
    def test_multi_tenant(self, sub, main):
        main_tenant_client = self.get_client(VALID_TOKEN_MAIN_TENANT)
        sub_tenant_client = self.get_client(VALID_TOKEN_SUB_TENANT)

        assert_that(
            calling(sub_tenant_client.backends.delete_source).with_args('google', main['uuid']),
            raises(Exception).matching(HTTP_404)
        )

        assert_that(
            calling(main_tenant_client.backends.delete_source).with_args(
                'google', main['uuid'], tenant_uuid=SUB_TENANT,
            ),
            raises(Exception).matching(HTTP_404)
        )

        assert_that(
            calling(main_tenant_client.backends.delete_source).with_args('google', sub['uuid']),
            not_(raises(Exception)),
        )


class TestList(BaseGoogleCRUDTestCase):

    def list_(self, *args, **kwargs):
        return self.client.backends.list_sources('google', *args, **kwargs)

    @fixtures.google_source(name='abc')
    @fixtures.google_source(name='bcd')
    @fixtures.google_source(name='cde')
    def test_searches(self, c, b, a):
        assert_that(self.list_(), has_entries(
            items=contains_inanyorder(a, b, c),
            total=3,
            filtered=3,
        ))

        assert_that(self.list_(name='abc'), has_entries(
            items=contains(a),
            total=3,
            filtered=1,
        ))

        assert_that(self.list_(uuid=c['uuid']), has_entries(
            items=contains(c),
            total=3,
            filtered=1,
        ))

        assert_that(self.list_(search='b'), has_entries(
            items=contains_inanyorder(a, b),
            total=3,
            filtered=2,
        ))

    @fixtures.google_source(name='abc')
    @fixtures.google_source(name='bcd')
    @fixtures.google_source(name='cde')
    def test_pagination(self, c, b, a):
        assert_that(self.list_(order='name'), has_entries(
            items=contains(a, b, c),
            total=3,
            filtered=3,
        ))

        assert_that(self.list_(order='name', direction='desc'), has_entries(
            items=contains(c, b, a),
            total=3,
            filtered=3,
        ))

        assert_that(self.list_(order='name', limit=2), has_entries(
            items=contains(a, b),
            total=3,
            filtered=3,
        ))

        assert_that(self.list_(order='name', offset=2), has_entries(
            items=contains(c),
            total=3,
            filtered=3,
        ))

    @fixtures.google_source(name='abc', token=VALID_TOKEN_MAIN_TENANT)
    @fixtures.google_source(name='bcd', token=VALID_TOKEN_MAIN_TENANT)
    @fixtures.google_source(name='cde', token=VALID_TOKEN_SUB_TENANT)
    def test_multi_tenant(self, c, b, a):
        main_tenant_client = self.get_client(VALID_TOKEN_MAIN_TENANT)
        sub_tenant_client = self.get_client(VALID_TOKEN_SUB_TENANT)

        assert_that(
            main_tenant_client.backends.list_sources('google'),
            has_entries(
                items=contains_inanyorder(a, b),
                total=2,
                filtered=2,
            )
        )

        assert_that(
            main_tenant_client.backends.list_sources('google', recurse=True),
            has_entries(
                items=contains_inanyorder(a, b, c),
                total=3,
                filtered=3,
            )
        )

        assert_that(
            main_tenant_client.backends.list_sources('google', tenant_uuid=SUB_TENANT),
            has_entries(
                items=contains_inanyorder(c),
                total=1,
                filtered=1,
            )
        )

        assert_that(
            sub_tenant_client.backends.list_sources('google'),
            has_entries(
                items=contains_inanyorder(c),
                total=1,
                filtered=1,
            )
        )

        assert_that(
            sub_tenant_client.backends.list_sources('google', recurse=True),
            has_entries(
                items=contains_inanyorder(c),
                total=1,
                filtered=1,
            )
        )


class TestPost(BaseGoogleCRUDTestCase):

    valid_body = {'name': 'google'}

    def test_invalid_body(self):
        try:
            self.client.backends.create_source('google', {})
        except Exception as e:
            assert_that(e.response.status_code, equal_to(400))
            assert_that(e.response.json(), has_entries(
                message=ANY,
                error_id='invalid-data',
                details=has_entries(name=ANY),
            ))
        else:
            self.fail('Should have raised')

    def test_minimal_body(self):
        with self.source(self.client, self.valid_body) as source:
            assert_that(source, has_entries(
                uuid=uuid_(),
                name='google',
                auth=has_entries(
                    host='localhost',
                    port=9497,
                    verify_certificate=True,
                ),
            ))

    def test_duplicate(self):
        with self.source(self.client, self.valid_body):
            assert_that(
                calling(self.client.backends.create_source).with_args('google', self.valid_body),
                raises(Exception).matching(HTTP_409),
            )

    def test_multi_tenant(self):
        main_tenant_client = self.get_client(VALID_TOKEN_MAIN_TENANT)
        sub_tenant_client = self.get_client(VALID_TOKEN_SUB_TENANT)

        with self.source(main_tenant_client, self.valid_body) as result:
            assert_that(result, has_entries(uuid=uuid_(), tenant_uuid=MAIN_TENANT))

        with self.source(main_tenant_client, self.valid_body, tenant_uuid=SUB_TENANT) as result:
            assert_that(result, has_entries(uuid=uuid_(), tenant_uuid=SUB_TENANT))

        with self.source(sub_tenant_client, self.valid_body) as result:
            assert_that(result, has_entries(uuid=uuid_(), tenant_uuid=SUB_TENANT))

        assert_that(
            calling(sub_tenant_client.backends.create_source).with_args(
                'google', self.valid_body, tenant_uuid=MAIN_TENANT,
            ),
            raises(Exception).matching(HTTP_401),
        )

        with self.source(main_tenant_client, self.valid_body):
            assert_that(
                calling(sub_tenant_client.backends.create_source).with_args(
                    'google', self.valid_body,
                ),
                not_(raises(Exception)),
            )

    @contextmanager
    def source(self, client, *args, **kwargs):
        source = client.backends.create_source('google', *args, **kwargs)
        try:
            yield source
        finally:
            try:
                client.backends.delete_source('google', source['uuid'])
            except Exception as e:
                response = getattr(e, 'response', None)
                status_code = getattr(response, 'status_code', None)
                if status_code != 404:
                    raise


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
            'first_matched_columns': ['numbers'],
            'format_columns': {
                'reverse': "{name}",
                'phone_mobile': "{numbers_by_label[mobile]}",
                'phone': '{numbers[0]}',
                'email': '{emails[0]}',
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

    def test_given_source_when_get_then_ok(self):
        config = self.config()

        created = self.client.backends.create_source(backend=self.BACKEND, body=config)

        source = self.client.backends.get_source(backend=self.BACKEND, source_uuid=created['uuid'])
        assert_that(source, equal_to(created))

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

        updated = self.client.backends.get_source(backend=self.BACKEND, source_uuid=source['uuid'])
        assert_that(updated, has_entries(
            uuid=source['uuid'],
            name='a-new-name',
        ))
