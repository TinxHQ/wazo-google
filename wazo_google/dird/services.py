# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging
import uuid

import requests

from xivo_auth_client import Client as Auth

from .exceptions import GoogleTokenNotFoundException, UnexpectedEndpointException


logger = logging.getLogger(__name__)


class GoogleService:

    USER_AGENT = 'wazo_ua/1.0'

    def get_contacts_with_term(self, google_token, term, url):
        headers = self.headers(google_token)
        query_params = {
            "search": term
        }
        try:
            response = requests.get(url, headers=headers, params=query_params)
            if response.status_code == 200:
                logger.debug('Sucessfully fetched contacts from google')
                return response.json().get('value', [])
            else:
                return []
        except requests.exceptions.RequestException as e:
            logger.error('Unable to get contacts from this endpoint: %s, error : %s', url, e)
            return []

    def get_contacts(self, google_token, url):
        headers = self.headers(google_token)
        try:
            response = requests.get(url, headers=headers)
            if response.status_code == 200:
                logger.debug('Successfully fetched contacts from google')
                return response.json().get('value', [])
            else:
                logger.error('An error occured while fetching information from google endpoint')
                raise UnexpectedEndpointException(endpoint=url, error_code=response.status_code)
        except requests.exceptions.RequestException:
            raise UnexpectedEndpointException(endpoint=url)

    def headers(self, google_token):
        return {
            'User-Agent': self.USER_AGENT,
            'Authorization': 'Bearer {0}'.format(google_token),
            'Accept': 'application/json',
            'client-request-id': str(uuid.uuid4),
            'return-client-request-id': 'true'
        }


def get_google_access_token(user_uuid, wazo_token, **auth_config):
    try:
        auth = Auth(token=wazo_token, **auth_config)
        return auth.external.get('google', user_uuid).get('access_token')
    except requests.HTTPError as e:
        logger.error('Google token could not be fetched from wazo-auth, error: %s', e)
        raise GoogleTokenNotFoundException(user_uuid)
    except requests.exceptions.ConnectionError as e:
        logger.error(
            'Unable to connect auth-client for the given parameters: %s, error: %s.',
            auth_config, e,
        )
        raise GoogleTokenNotFoundException(user_uuid)
    except requests.exceptions.RequestException as e:
        logger.error('Error occured while connecting to wazo-auth, error: %s', e)


class ContactFormatter:

    chars_to_remove = [' ', '-', '(', ')']

    def format(self, contact):
        return {
            'name': self._extract_name(contact),
            'numbers': self._extract_numbers(contact),
            'emails': self._extract_emails(contact),
        }

    def _extract_emails(self, contact):
        emails = {}

        for email in contact.get('gd$email', []):
            type_ = self._extract_type(email)
            if not type_:
                continue

            email = email.get('address')
            if not email:
                continue

            emails[type_] = email

        return emails

    def _extract_numbers(self, contact):
        numbers = {}
        for number in contact.get('gd$phoneNumber', []):
            type_ = self._extract_type(number)
            if not type_:
                continue

            number = number.get('$t')
            if not number:
                continue

            for char in self.chars_to_remove:
                number = number.replace(char, '')

            numbers[type_] = number

        return numbers

    def _extract_name(self, contact):
        return contact.get('title', {}).get('$t', '')

    def _extract_type(self, entry):
        rel = entry.get('rel')
        if rel:
            _, type_ = rel.rsplit('#', 1)
        else:
            type_ = entry.get('label')
        return type_
