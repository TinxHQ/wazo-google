# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

import logging
import requests
import time

from flask import request
from datetime import datetime, timedelta

from xivo.mallow import fields
from xivo.mallow import validate
from wazo_auth import exceptions, http, schemas

logger = logging.getLogger(__name__)


class GooglePostSchema(schemas.BaseSchema):

    scope = fields.List(fields.String(min=1, max=512))


class GoogleAuth(http.ErrorCatchingResource):

    auth_type = 'google'
    scope = 'https://www.googleapis.com/auth/contacts'

    def __init__(self, external_auth_service, config):
        self.client_id = config['google']['client_id']
        self.client_secret = config['google']['client_secret']
        self.external_auth_service = external_auth_service

        self.new_device_url = 'https://accounts.google.com/o/oauth2/device/code'

    @http.required_acl('auth.users.{user_uuid}.external.google.delete')
    def delete(self, user_uuid):
        self.external_auth_service.delete(user_uuid, self.auth_type)
        return '', 204

    @http.required_acl('auth.users.{user_uuid}.external.google.read')
    def get(self, user_uuid):
        data = self.external_auth_service.get(user_uuid, self.auth_type)

        token = data.get('access_token')
        expiration = data.get('token_expiration')

        if not token:
            return self._create_first_token(user_uuid, data)

        if self._is_token_expired(expiration):
            return self._refresh_token(user_uuid, data)

        return self._new_get_response(data)

    def _create_first_token(self, user_uuid, data):
        logger.debug('creating new token')
        device_code = data['device_code']
        data = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': device_code,
            'grant_type': 'http://oauth.net/grant_type/device/1.0'
        }

        url = 'https://www.googleapis.com/oauth2/v4/token'
        r = requests.post(url, data=data)

        logger.debug('token info: %s', r.json())
        token_data = r.json()

        data['access_token'] = token_data['access_token']
        data['refresh_token'] = token_data['refresh_token']
        data['token_expiration'] = self._get_timestamp_expiration(token_data['expires_in'])

        self.external_auth_service.update(user_uuid, self.auth_type, data)

        return self._new_get_response(data)

    @http.required_acl('auth.users.{user_uuid}.external.google.create')
    def post(self, user_uuid):
        logger.info('User(%s) is creating a new device_code for Google', str(user_uuid))
        args, errors = GooglePostSchema().load(request.get_json())
        if errors:
            raise exceptions.UserParamException.from_errors(errors)

        data = self._new_device()
        stored_data = dict(scope=args['scope'], **data)
        self.external_auth_service.create(user_uuid, self.auth_type, stored_data)
        logger.debug('new device_code stored for User(%s)', str(user_uuid))

        return {
            'verification_url': data['verification_url'],
            'user_code': data['user_code'],
        }, 200

    @http.required_acl('auth.users.{user_uuid}.external.google.edit')
    def put(self, user_uuid):
        data = request.get_json(force=True)
        return self.external_auth_service.update(user_uuid, self.auth_type, data), 200

    def _new_device(self):
        data = {
            'client_id': self.client_id,
            'scope': self.scope
        }
        r = requests.post(self.new_device_url, data=data)
        return r.json()

    def _refresh_token(self, user_uuid, data):
        refresh = {
          'refresh_token': data['refresh_token'],
          'client_id': self.client_id,
          'client_secret': self.client_secret,
          'grant_type': 'refresh_token'
        }

        url = 'https://www.googleapis.com/oauth2/v4/token'
        r = requests.post(url, data=refresh)

        logger.debug('refresh token info: %s', r.json())
        data['access_token'] = r.json()['access_token']
        data['token_expiration'] = self._get_timestamp_expiration(r.json()['expires_in'])

        self.external_auth_service.update(user_uuid, self.auth_type, data)

        return self._new_get_response(data)

    def _get_timestamp_expiration(self, expires_in):
        token_expiration_date = datetime.now() + timedelta(seconds=expires_in)
        return time.mktime(token_expiration_date.timetuple())

    def _is_token_expired(self, token_expiration):
        if token_expiration is None:
           return True
        return time.mktime(datetime.now().timetuple()) > token_expiration

    @staticmethod
    def _new_get_response(data):
        return {
            'access_token': data['access_token'],
            'expiration': data['token_expiration'],
            'scope': data.get('scope'),
        }, 200


class Plugin(object):

    def load(self, dependencies):
        api = dependencies['api']
        args = (dependencies['external_auth_service'], dependencies['config'])

        api.add_resource(GoogleAuth, '/users/<uuid:user_uuid>/external/google', resource_class_args=args)
