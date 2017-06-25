

{% set keyring_file = salt['keyring.file']('osd') %}
{{ keyring_file}}:
  file.managed:
    - source: salt://ceph/osd/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      secret: {{ salt['keyring.secret'](keyring_file) }}
    - fire_event: True

{% set keyring_file = "/srv/salt/ceph/osd/cache/ceph.client.storage.keyring" %}
{{ keyring_file}}:
  file.managed:
    - source: salt://ceph/osd/files/storage.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      secret: {{ salt['keyring.secret'](keyring_file) }}
    - fire_event: True



