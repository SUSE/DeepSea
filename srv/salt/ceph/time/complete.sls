

salt/ceph/step/time/{{ grains['host'] }}/complete:
  event.send:
    - data:
        status: "time step complete"


