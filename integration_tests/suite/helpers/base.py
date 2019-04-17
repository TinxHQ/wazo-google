# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import requests

from xivo_test_helpers.asset_launching_test_case import AssetLaunchingTestCase
from xivo_auth_client import Client


class BaseTestCase(AssetLaunchingTestCase):

    assets_root = os.path.join(os.path.dirname(__file__), '../..', 'assets')
    service = 'auth'
    username = 'mario'
    password = 'mario'

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        port = cls.service_port(9497, 'auth')
        key = cls.docker_exec(['cat', '/var/lib/wazo-auth/init.key']).decode('utf-8')
        url = 'https://localhost:{}/0.1/init'.format(port)
        headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}
        body = {'key': key, 'username': cls.username, 'password': cls.password}
        response = requests.post(url, json=body, headers=headers, verify=False)
        response.raise_for_status()

        cls.client = Client(
            'localhost',
            port=port,
            verify_certificate=False,
            username=cls.username,
            password=cls.password
            )
        token_data = cls.client.token.new(backend='wazo_user', expiration=7200)
        cls.admin_user_uuid = token_data['metadata']['uuid']
        cls.client.set_token(token_data['token'])

        cls.top_tenant_uuid = cls.get_top_tenant()['uuid']

    @classmethod
    def get_top_tenant(cls):
        return cls.client.tenants.list(name='master')['items'][0]
