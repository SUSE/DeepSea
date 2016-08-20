
salt/ceph/stage/admin/{{ grains['host'] }}/begin:
  event.send:
    - data:
        status: "admin stage begins"


