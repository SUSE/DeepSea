

{% for role in salt['rgw.configurations']() %}

/var/lib/ceph/radosgw/ceph-{{ role }}/keyring:
  file.managed:
    - source:
      - salt://ceph/rgw/cache/client.{{ role }}.keyring
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - fire_event: True

{% endfor %}
