

{% for role in salt['pillar.get']('rgw_configurations', [ 'rgw' ]) %}

/var/lib/ceph/radosgw/ceph-{{ role + "." + grains['host'] }}/keyring:
  file.managed:
    - source:
      - salt://ceph/rgw/cache/client.{{ role + "." +  grains['host'] }}.keyring
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - fire_event: True

{% endfor %}
