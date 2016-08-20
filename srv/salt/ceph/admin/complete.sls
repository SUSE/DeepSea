

salt/ceph/stage/admin/{{ grains['host'] }}/complete:
  event.send:
    - data:
        status: "admin stage complete"


