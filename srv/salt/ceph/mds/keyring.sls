
{% set keyring_name = "ceph.client.igw." + grains['host'] + ".keyring" %}

/var/lib/ceph/mds/ceph-{{ grains['host'] }}/keyring:
  file.managed:
    - source:
      - salt://ceph/mds/cache/{{ grains['host'] }}.keyring
    - template: jinja
    - user: ceph
    - group: ceph
    - mode: 600
    - makedirs: True
    - fire_event: True

