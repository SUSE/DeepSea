
salt/ceph/step/packages/{{ grains['host'] }}/begin:
  event.send:
    - data:
        status: "package step begins"


