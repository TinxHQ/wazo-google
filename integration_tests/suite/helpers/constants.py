# Copyright 2019 The Wazo Authors  (see the AUTHORS file)
# SPDX-License-Identifier: GPL-3.0-or-later

from hamcrest import has_properties

VALID_TOKEN_MAIN_TENANT = 'valid-token-master-tenant'
VALID_TOKEN_SUB_TENANT = 'valid-token-sub-tenant'
MAIN_TENANT = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee10'
SUB_TENANT = 'eeeeeeee-eeee-eeee-eeee-eeeeeeeeee11'
UNKNOWN_UUID = '00000000-0000-0000-0000-000000000000'

HTTP_400 = has_properties(response=has_properties(status_code=400))
HTTP_401 = has_properties(response=has_properties(status_code=401))
HTTP_404 = has_properties(response=has_properties(status_code=404))
HTTP_409 = has_properties(response=has_properties(status_code=409))

GOOGLE_CONTACT_LIST = {
    "feed": {
        "openSearch$totalResults": {"$t": "2"},
        "openSearch$startIndex": {"$t": "1"},
        "openSearch$itemsPerPage": {"$t": "10000"},
        "entry": [
            {
                "id": {"$t": "http://www.google.com/m8/feeds/contacts/peach%40bros.example.com/base/20aec7728b4f316b"},
                "title": {"$t": "Mario Bros", "type": "text"},
                "gd$email":[
                    {"address": "mario@bros.example.com", "rel": "http://schemas.google.com/g/2005#other"},
                ],
                "gd$phoneNumber": [
                    {"rel": "http://schemas.google.com/g/2005#mobile", "uri": "tel:+1-555-555-1234", "$t": "+1 555-555-1234"},
                    {"rel": "http://schemas.google.com/g/2005#home", "uri": "tel:+1-555-555-1111", "$t": "+1 5555551111"},
                ],
            },
            {
                "id": {"$t": "http://www.google.com/m8/feeds/contacts/peach%40bros.example.com/base/72b6b4840bf772e6"},
                "title": {"$t": "Luigi Bros", "type": "text"},
                "gd$email": [
                    {"address": "Luigi@bros.example.com", "rel": "http://schemas.google.com/g/2005#home"},
                    {"address": "luigi_bros@caramail.com", "label": "Old school"},
                ],
                "gd$phoneNumber": [
                    {"rel": "http://schemas.google.com/g/2005#mobile", "uri": "tel:+1-555-555-4567", "$t": "+1 555-555-4567"},
                    {"rel": "http://schemas.google.com/g/2005#home", "uri": "tel:+1-555-555-1111", "$t": "+1 5555551111"},
                    {"label": "Mushroom land land-line", "uri": "tel:+1-555-555-2222", "$t": "(555) 555-2222"},
                ],
            }
        ]
    }
}
