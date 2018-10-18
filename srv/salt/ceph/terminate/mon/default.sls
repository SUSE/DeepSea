
stop mon:
  service.dead:
    - name: ceph-mon@{{ grains['host'] }}


