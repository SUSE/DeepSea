
salt/ceph/stage/prep/{{ grains['host'] }}/begin:
  event.send:
    - data:
        status: "prep stage begins"


