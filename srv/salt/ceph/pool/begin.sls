
salt/ceph/step/pool/{{ grains['host'] }}/begin:
  event.send:
    - data:
        status: "pool step begins"


