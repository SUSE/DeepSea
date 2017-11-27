
{# The mon creation needs this key as well #}
{# Named the file the same as other components, there is only one keyring #}
{% set keyring_file = "/srv/salt/ceph/admin/cache/ceph.client.admin.keyring" %}
{{ keyring_file }}:
  file.managed:
    - source:
      - salt://ceph/admin/files/keyring.j2
    - template: jinja
    - user: {{ salt['deepsea.user']() }}
    - group: {{ salt['deepsea.group']() }}
    - mode: 600
    - makedirs: True
    - context:
      secret: {{ salt['keyring.secret'](keyring_file) }}
    - fire_event: True


