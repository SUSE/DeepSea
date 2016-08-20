
salt/ceph/stage/prep/{{ grains['host'] }}/begin:
  event.send:
    - data:
        status: "prep stage begins"

# Until order and require work for events, let's wait a moment so that
# we aren't sending the complete event before we have started

sleep:
  cmd.run:
    - name: "sleep 3"
    - require:
      - event: salt/ceph/stage/prep/{{ grains['host'] }}/begin

