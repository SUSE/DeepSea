
salt/ceph/step/mon/{{ grains['host'] }}/begin:
  event.send:
    - data:
        status: "mon step begins"


