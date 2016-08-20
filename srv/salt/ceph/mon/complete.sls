

salt/ceph/step/mon/{{ grains['host'] }}/complete:
  event.send:
    - data:
        status: "mon step complete"


