
start mgr {{ grains['host'] }}:
  service.running:
    - name: ceph-mgr@{{ grains['host'] }}

