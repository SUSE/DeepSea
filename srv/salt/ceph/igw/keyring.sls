
{% set keyring_name = "ceph.client.igw." + grains['host'] + ".keyring" %}

/etc/ceph/{{ keyring_name }}:
  file.managed:
    - source: 
      - salt://ceph/igw/cache/{{ keyring_name }}
    - user: root
    - group: root
    - mode: 600

