

salt/ceph/step/pool/{{ grains['host'] }}/complete:
  event.send:
    - data:
        status: "pool step complete"


