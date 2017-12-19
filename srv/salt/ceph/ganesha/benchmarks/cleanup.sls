
include:
  - ceph.tools.fio.cleanup

unmount nfs:
  mount.unmounted:
    - name: {{ salt['pillar.get']('benchmark:work-directory')}}

