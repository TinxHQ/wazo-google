# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

import logging

from wazo_dird.helpers import BaseBackendView

from .http import GoogleItem, GoogleList, GoogleContactList


logger = logging.getLogger(__name__)


class GoogleView(BaseBackendView):

    backend = 'google'
    item_resource = GoogleItem
    list_resource = GoogleList
    contact_list_resource = GoogleContactList

    def load(self, dependencies):
        super().load(dependencies)
        api = dependencies['api']
        config = dependencies['config']
        auth_config = config['auth']
        source_service = dependencies['services']['source']
        args = (auth_config, config, source_service)

        api.add_resource(
            self.contact_list_resource,
            "/backends/google/sources/<source_uuid>/contacts",
            resource_class_args=args,
        )
