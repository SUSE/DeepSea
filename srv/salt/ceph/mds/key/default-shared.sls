
{% set client = "mds.mds" %}
{% set keyring_file = salt['keyring.file']('mds', 'mds')  %}
{{ keyring_file}}:
  file.managed:
    - source:
      - salt://ceph/mds/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      client: {{ client }}
      secret: {{ salt['keyring.secret'](keyring_file) }}
    - fire_event: True



