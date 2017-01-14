
{# Note the ganesha role uses the corresponding rgw keyring #}

{% for role in salt['ganesha.configurations']() %}
{% rgw_role = salt['rgw.configuration'](role) %}

/var/lib/ceph/radosgw/ceph-{{ rgw_role + "." + grains['host'] }}/keyring:
  file.managed:
    - source:
      - salt://ceph/rgw/cache/client.{{ rgw_role + "." +  grains['host'] }}.keyring
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - fire_event: True

{% endfor %}
