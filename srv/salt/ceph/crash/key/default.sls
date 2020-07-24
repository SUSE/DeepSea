
{% set keyring_file = "/srv/salt/ceph/crash/cache/ceph.client.crash.keyring" %}
{{ keyring_file }}:
  file.managed:
    - source:
      - salt://ceph/crash/files/keyring.j2
    - template: jinja
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - context:
      secret: {{ salt['keyring.secret'](keyring_file) }}
    - fire_event: True


