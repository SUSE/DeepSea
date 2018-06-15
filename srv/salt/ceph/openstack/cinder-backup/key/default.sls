{% set keyring_file = salt['keyring.file']('cinder-backup') %}
{{ keyring_file}}:
  file.managed:
    - source: salt://ceph/openstack/cinder-backup/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      client: client.cinder-backup
      secret: {{ salt['keyring.secret'](keyring_file) }}
    - fire_event: True

