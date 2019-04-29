# wazo-google plugin

This is a plugin for Wazo that adds external authentication routes to wazo-auth for Google and contacts to wazo-dird.


## auth plugin

This plugin adds routes to manage google authentication.


## dird plugin

This plugin adds Google contact to search results from wazo-auth


### Configuration

The `client_id` and `client_secret` for the google external auth can be configured using the
`/external/google/config` URL from wazo-auth.


## Wazo-SDK

Theses lines should be added to `wazo-sdk/project.yml` in order to overwrite other configurations. Therefore, the files in `/etc` should also exist.

```yml
wazo-google:
  python3: true
  bind:
    etc/wazo-auth/conf.d/google.yml: /etc/wazo-auth/conf.d/google.yml
```

# Running integration tests
You need Docker installed.

```sh
cd integration_tests
pip install -U -r test-requirements.txt
make test-setup
make test
```
