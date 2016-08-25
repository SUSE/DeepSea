

salt/ceph/stage/prep/{{ grains['host'] }}/complete:
  event.send:
    - data:
        status: "prep stage complete"


