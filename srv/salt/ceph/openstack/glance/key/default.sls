{% set prefix = pillar['openstack_prefix'] + "-" if 'openstack_prefix' in pillar else "" %}
{% set keyring_file = salt['keyring.file']('glance', prefix) %}
{{ keyring_file}}:
  file.managed:
    - source: salt://ceph/openstack/glance/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      client: client.{{ prefix }}glance
      secret: {{ salt['keyring.secret'](keyring_file) }}
      prefix: "{{ prefix }}"
    - fire_event: True

