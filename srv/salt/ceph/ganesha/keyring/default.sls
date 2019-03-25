{% for role in salt['ganesha.configurations']() %}

{% set keyring_name = "ceph.client." + role + "." + grains['host'] + ".keyring" %}
/etc/ceph/{{ keyring_name }}:
  file.managed:
    - source:
      - salt://ceph/ganesha/cache/{{ keyring_name }}
    - user: root
    - group: root
    - mode: 600
    - fire_event: True


{% set rgw_role = salt['rgw.configuration'](role) %}
{%if rgw_role %}
/var/lib/ceph/radosgw/ceph-{{ role + "." + grains['host'] }}/keyring:
  file.managed:
    - source:
      - salt://ceph/ganesha/cache/client.{{ role + "." +  grains['host'] }}.keyring
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - fire_event: True
{% endif %}

{% endfor %}
