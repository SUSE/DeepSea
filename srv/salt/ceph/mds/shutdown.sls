shutdown daemon:
  service.dead:
    - name: ceph-mds@{{ grains['host'] }}
