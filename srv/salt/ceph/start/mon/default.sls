
start mon:
  service.running:
    - name: ceph-mon@{{ grains['host'] }}


