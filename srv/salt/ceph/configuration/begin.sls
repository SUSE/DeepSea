
salt/ceph/step/configuration/{{ grains['host'] }}/begin:
  event.send:
    - data:
        status: "configuration step begins"


