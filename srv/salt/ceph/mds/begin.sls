
salt/ceph/step/mds/{{ grains['host'] }}/begin:
  event.send:
    - data:
        status: "mds step begins"


