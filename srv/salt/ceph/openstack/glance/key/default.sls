
{% set keyring_file = salt['keyring.file']('glance') %}
{{ keyring_file}}:
  file.managed:
    - source: salt://ceph/openstack/glance/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      secret: {{ salt['keyring.secret'](keyring_file) }}
    - fire_event: True

