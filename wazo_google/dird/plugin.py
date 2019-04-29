# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from wazo_dird import BaseSourcePlugin, make_result_class

from .exceptions import GoogleTokenNotFoundException
from . import services

logger = logging.getLogger(__name__)


class GooglePlugin(BaseSourcePlugin):

    def load(self, dependencies):
        config = dependencies['config']
        self.auth = config['auth']
        self.name = config['name']
        self.google = services.GoogleService()
        self.unique_column = 'id'

        format_columns = dependencies['config'].get(self.FORMAT_COLUMNS, {})
        if 'reverse' not in format_columns:
            logger.info(
                'no "reverse" column has been configured on %s will use "name"',
                self.name
            )
            format_columns['reverse'] = '{name}'

        self._SourceResult = make_result_class(
            'google',
            self.name,
            self.unique_column,
            format_columns,
        )

        self._searched_columns = config.get(self.SEARCHED_COLUMNS, [])
        if not self._searched_columns:
            logger.info(
                'no "searched_columns" configured on "%s" no results will be matched',
                self.name,
            )

        self._first_matched_columns = config.get(self.FIRST_MATCHED_COLUMNS, [])
        if not self._first_matched_columns:
            logger.info(
                'no "first_matched_columns" configured on "%s" no results will be matched',
                self.name,
            )

    def search(self, term, args=None):
        logger.debug('Searching term=%s', term)
        try:
            google_token = self._get_google_token(**args)
        except GoogleTokenNotFoundException:
            return []

        contacts = self.google.get_contacts_with_term(google_token, term)
        lowered_term = term.lower()
        filtered_contacts = [c for c in contacts if self._search_match_predicate(c, lowered_term)]

        return [self._SourceResult(c) for c in filtered_contacts]

    def list(self, unique_ids, args=None):
        try:
            google_token = self._get_google_token(**args)
        except GoogleTokenNotFoundException:
            return []

        contacts = self.google.get_contacts(google_token)
        filtered_contacts = [c for c in contacts if c[self.unique_column] in unique_ids]

        return [self._SourceResult(contact) for contact in filtered_contacts]

    def first_match(self, term, args=None):
        if not self._first_matched_columns:
            logger.debug(
                '%s is a source for reverse lookups but the not have a "first_matched_columns"',
                self.name,
            )
            return

        try:
            google_token = self._get_google_token(**args)
        except GoogleTokenNotFoundException:
            logger.debug('could not find a matching google token, aborting first_match')
            return None

        contacts = self.google.get_contacts(google_token)
        lowered_term = term.lower()

        for contact in contacts:
            if self._first_match_predicate(lowered_term, contact):
                return self._SourceResult(contact)

    def _first_match_predicate(self, term, contact):
        for column in self._first_matched_columns:
            column_value = contact.get(column) or ''
            if term == str(column_value).lower():
                return True
        return False

    def _get_google_token(self, xivo_user_uuid, token=None, **ignored):
        if not token:
            logger.debug('Unable to search through Google without a token.')
            raise GoogleTokenNotFoundException()

        return services.get_google_access_token(xivo_user_uuid, token, **self.auth)

    def _search_match_predicate(self, contact, term):
        for field in self._searched_columns:
            column_value = contact.get(field) or ''
            if not isinstance(column_value, dict):
                if term in column_value.lower():
                    return True
            else:
                for value in column_value.values():
                    if term in value.lower():
                        return True
        return False
