
salt/ceph/step/osd/{{ grains['host'] }}/begin:
  event.send:
    - data:
        status: "osd step begins"


