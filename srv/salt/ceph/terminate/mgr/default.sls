
stop mgr {{ grains['host'] }}:
  service.dead:
    - name: ceph-mgr@{{ grains['host'] }}

