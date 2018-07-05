#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright 2017 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0+

from setuptools import find_packages
from setuptools import setup

setup(
    name='wazo_google',
    version='0.1',
    description='Wazo Google connector',

    author='Wazo Authors',
    author_email='dev@wazo.community',

    url='http://wazo.community',

    packages=find_packages(),
    include_package_data=True,
    package_data={
        'wazo_google': ['*/api.yml'],
    },
    entry_points={
        'wazo_auth.external_auth': [
            'google = wazo_google.auth.plugin:Plugin',
        ],
        'wazo_dird.backends': [
            'google = wazo_google.dird.plugin:Plugin',
        ],
    }
)
