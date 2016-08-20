
salt/ceph/stage/discovery/{{ grains['host'] }}/begin:
  event.send:
    - data:
        status: "discovery stage begins"


