{% for role in salt['ganesha.configurations']() %}
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
