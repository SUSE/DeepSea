

salt/ceph/stage/discovery/{{ grains['host'] }}/complete:
  event.send:
    - data:
        status: "discovery stage complete"


