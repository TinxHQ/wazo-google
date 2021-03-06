# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import pprint

import requests
from hamcrest import assert_that, empty

from .helpers.base import BaseTestCase


class TestDirdDocumentation(BaseTestCase):

    asset = 'documentation'

    def test_documentation_errors(self):
        api_url = 'https://dird:9489/0.1/api/api.yml'
        self._validate_api(api_url)

    def _validate_api(self, url):
        port = self.service_port(8080, 'swagger-validator')
        validator_url = 'http://localhost:{port}/debug'.format(port=port)
        response = requests.get(validator_url, params={'url': url})
        assert_that(response.json(), empty(), pprint.pformat(response.json()))
