
{% set keyring_file = "/srv/salt/ceph/openattic/cache/ceph.client.openattic.keyring" %}
{{ keyring_file }}:
  file.managed:
    - source: 
      - salt://ceph/openattic/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      secret: {{ salt['keyring.secret'](keyring_file) }}
    - fire_event: True


