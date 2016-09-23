
{% set admin_keyring = "/srv/salt/ceph/admin/cache/ceph.client.admin.keyring" %}

{% for host in salt.saltutil.runner('select.minions', cluster='ceph', roles='mon', host=True) %}
{% set keyring_file = "/srv/salt/ceph/mon/cache/" + host + ".keyring" %}
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

{% endfor %}


