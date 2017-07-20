
{% set keyring_file = "/srv/salt/ceph/mon/cache/mon.keyring" %}
{{ keyring_file }}:
  file.managed:
    - source:
      - salt://ceph/mon/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      mon_secret: {{ salt['keyring.secret'](keyring_file) }}
    - fire_event: True

{{ keyring_file }} append admin keyring:
  file.append:
    - name: {{ keyring_file }}
    - source: salt://ceph/admin/cache/ceph.client.admin.keyring
