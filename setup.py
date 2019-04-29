#!/usr/bin/env python3
# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from setuptools import find_packages
from setuptools import setup

setup(
    name='wazo_google',
    version='1.1.0',
    description='Wazo Google connector',

    author='Wazo Authors',
    author_email='dev@wazo.io',

    url='http://wazo.io',

    packages=find_packages(),
    include_package_data=True,
    package_data={
        'wazo_google': ['*/api.yml'],
    },
    entry_points={
        'wazo_auth.external_auth': [
            'google = wazo_google.auth.plugin:GooglePlugin',
        ],
        'wazo_dird.backends': [
            'google = wazo_google.dird.plugin:GooglePlugin',
        ],
        'wazo_dird.views': [
            'google_view = wazo_google.dird.view:GoogleView'
        ]
    }
)
