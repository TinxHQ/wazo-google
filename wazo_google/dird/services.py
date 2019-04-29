# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

import requests

from xivo_auth_client import Client as Auth

from .exceptions import GoogleTokenNotFoundException, UnexpectedEndpointException


logger = logging.getLogger(__name__)


class GoogleService:

    USER_AGENT = 'wazo_ua/1.0'

    def __init__(self):
        self.formatter = ContactFormatter()

    def get_contacts_with_term(self, google_token, term, url):
        url = 'https://google.com/m8/feeds/contacts/default/full'
        headers = self.headers(google_token)
        query_params = {
            'q': term,
            'alt': 'json',
            'max-results': 10000,
        }

        response = requests.get(url, headers=headers, params=query_params)
        if response.status_code != 200:
            return []

        logger.debug('Sucessfully fetched contacts from google')
        for contact in response.json().get('feed', {}).get('entry', []):
            yield self.formatter.format(contact)

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
            'Authorization': 'Bearer {}'.format(google_token),
            'Accept': 'application/json',
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
            'id': 42,
            'name': self._extract_name(contact),
            'numbers': self._extract_numbers(contact),
            'emails': self._extract_emails(contact),
        }

    @classmethod
    def _extract_emails(cls, contact):
        emails = {}

        for email in contact.get('gd$email', []):
            type_ = cls._extract_type(email)
            if not type_:
                continue

            email = email.get('address')
            if not email:
                continue

            emails[type_] = email

        return emails

    @classmethod
    def _extract_numbers(cls, contact):
        numbers = {}
        for number in contact.get('gd$phoneNumber', []):
            type_ = cls._extract_type(number)
            if not type_:
                continue

            number = number.get('$t')
            if not number:
                continue

            for char in cls.chars_to_remove:
                number = number.replace(char, '')

            numbers[type_] = number

        return numbers

    @staticmethod
    def _extract_name(contact):
        return contact.get('title', {}).get('$t', '')

    @staticmethod
    def _extract_type(entry):
        rel = entry.get('rel')
        if rel:
            _, type_ = rel.rsplit('#', 1)
        else:
            type_ = entry.get('label')
        return type_
