
salt/ceph/step/time/{{ grains['host'] }}/begin:
  event.send:
    - data:
        status: "time step begins"


