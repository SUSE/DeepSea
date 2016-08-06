

salt/ceph/step/packages/{{ grains['host'] }}/complete:
  event.send:
    - data:
        status: "package step complete"


