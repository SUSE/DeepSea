
stop mds {{ grains['host'] }}:
  service.dead:
    - name: ceph-mds@{{ grains['host'] }}

