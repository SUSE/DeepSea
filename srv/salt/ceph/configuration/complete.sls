

salt/ceph/step/configuration/{{ grains['host'] }}/complete:
  event.send:
    - data:
        status: "configuration step complete"


