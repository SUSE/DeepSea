

salt/ceph/stage/rgw/{{ grains['host'] }}/complete:
  event.send:
    - data:
        status: "rgw stage complete"


