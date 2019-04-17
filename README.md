# wazo-google plugin

### auth plugin

This plugin adds routes to manage google authentication.

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
