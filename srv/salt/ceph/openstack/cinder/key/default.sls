{% set prefix = pillar['openstack_prefix'] + "-" if 'openstack_prefix' in pillar else "" %}
{% set keyring_file = salt['keyring.file']('cinder', prefix) %}
{{ keyring_file}}:
  file.managed:
    - source: salt://ceph/openstack/cinder/files/keyring.j2
    - template: jinja
    - user: salt
    - group: salt
    - mode: 600
    - makedirs: True
    - context:
      client: client.{{ prefix }}cinder
      secret: {{ salt['keyring.secret'](keyring_file) }}
      prefix: "{{ prefix }}"
    - fire_event: True

