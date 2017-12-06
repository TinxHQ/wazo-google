# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+


from xivo_dird import BaseSourcePlugin
from xivo_dird import make_result_class
import logging
import httplib2

from oauth2client.client import AccessTokenCredentials
from xivo_auth_client import Client as Auth
from apiclient import discovery


logger = logging.getLogger(__name__)


class Plugin(BaseSourcePlugin):

    def load(self, config):
        self.config = config['config']['google_config']
        self.name = config['config']['name']
        self.token = self.get_token()

        unique_column = None
        format_columns = config['config'].get(self.FORMAT_COLUMNS, {})

        self._SourceResult = make_result_class(
            self.name,
            unique_column,
            format_columns,
            )


    def get_token(self):
        auth = Auth(
            self.config['auth']['host'],
            username=self.config['auth']['username'],
            password=self.config['auth']['password'],
            verify_certificate=False)
        return auth.token.new('xivo_service', expiration=3600)

    def get_external_token(self, user_uuid):
        token = None
        auth = Auth(self.config['auth']['host'], verify_certificate=False, token=self.token['token'])
        try:
            token = auth.external.get('google', user_uuid)
        except:
            print('Request new token')
            self.token = self.get_token()
            auth = Auth(self.config['auth']['host'], verify_certificate=False, token=self.token['token'])
            token = auth.external.get('google', user_uuid)

        return token

    def name(self):
        return self.name

    def search(self, term, profile=None, args=None):
        logger.debug("search term=%s profile=%s", term, profile)
        user_uuid = profile.get('xivo_user_uuid')
        token = self.get_external_token(user_uuid)

        gtoken = token.get('access_token')
        credentials = AccessTokenCredentials(gtoken, 'wazo_ua/1.0')
        http = httplib2.Http()
        http = credentials.authorize(http)

        service = discovery.build('people', 'v1', http=http,
            discoveryServiceUrl='https://people.googleapis.com/$discovery/rest', cache_discovery=False)

        results = service.people().connections().list(
            resourceName='people/me',
            pageSize=10,
            personFields='names,emailAddresses').execute()
        connections = results.get('connections', [])

        res = []
        for person in connections:
            names = person.get('names', [])
            if len(names) > 0:
                name = names[0].get('displayName')
                res.append({
                    'firstname': '',
                    'lastname': name,
                    'job': '',
                    'phone': '',
                    'email': '',
                    'entity': '',
                    'mobile': '',
                    'fax': '',
                    })

        return [self._source_result_from_content(content) for content in res]

    def first_match(self, term, args=None):
        return None

    def _source_result_from_content(self, content):
        return self._SourceResult(content)
