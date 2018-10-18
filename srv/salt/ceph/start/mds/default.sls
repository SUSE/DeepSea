
start mds {{ grains['host'] }}:
  service.running:
    - name: ceph-mds@{{ grains['host'] }}


