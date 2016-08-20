

salt/ceph/step/mds/{{ grains['host'] }}/complete:
  event.send:
    - data:
        status: "mds step complete"


