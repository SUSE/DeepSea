
salt/ceph/stage/configure/{{ grains['host'] }}/begin:
  event.send:
    - data:
        status: "configure stage begins"


