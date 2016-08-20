
salt/ceph/step/rgw/{{ grains['host'] }}/begin:
  event.send:
    - data:
        status: "rgw step begins"


