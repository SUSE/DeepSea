

salt/ceph/stage/configure/{{ grains['host'] }}/complete:
  event.send:
    - data:
        status: "configure stage complete"


