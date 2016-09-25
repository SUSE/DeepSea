
{% set admin_keyring = "/srv/salt/ceph/admin/cache/ceph.client.admin.keyring" %}

{% set keyring_file = "/srv/salt/ceph/mon/cache/mon.keyring" %}
{{ keyring_file}}:
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
      admin_secret: {{ salt['keyring.secret'](admin_keyring) }}
    - fire_event: True



