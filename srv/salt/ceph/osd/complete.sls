

salt/ceph/stage/osd/{{ grains['host'] }}/complete:
  event.send:
    - data:
        status: "osd stage complete"


