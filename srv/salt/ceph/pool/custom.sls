
wait:
  module.run:
    - name: wait.out
    - kwargs:
        'status': "HEALTH_ERR"
    - fire_event: True

backstore:
  cmd.run:
    - name: "rbd -p rbd create archive --size=1024"
    - unless: "rbd -p rbd ls | grep -q archive$"
    - fire_event: True

archive1:
  cmd.run:
    - name: "rbd -p rbd create archive1 --size=768"
    - unless: "rbd -p rbd ls | grep -q archive1$"
    - fire_event: True

archive2:
  cmd.run:
    - name: "rbd -p rbd create archive2 --size=512"
    - unless: "rbd -p rbd ls | grep -q archive2$"
    - fire_event: True

erasure profile:
  cmd.run:
    - name: "ceph osd erasure-code-profile set three-one k=3 m=1"
    - unless: "ceph osd erasure-code-profiles ls | grep -q three-one"
    - fire_event: True

swimming:
  cmd.run:
    - name: "ceph osd pool create swimming 128 erasure three-one"
    - unless: "ceph osd pool ls | grep -q swimming$"
    - fire_event: True

cache:
  cmd.run:
    - name: "ceph osd pool create swimming-cache 256 256"
    - unless: "ceph osd pool ls | grep -q swimming-cache"
    - fire_event: True

cache tier:
  cmd.run:
    - name: "ceph osd tier add swimming swimming-cache"
    - fire_event: True

cache mode:
  cmd.run:
    - name: "ceph osd tier cache-mode swimming-cache writeback"
    - fire_event: True

overlay:
  cmd.run:
    - name: "ceph osd tier set-overlay swimming swimming-cache"
    - fire_event: True

hit_set_type:
  cmd.run:
    - name: "ceph osd pool set swimming-cache hit_set_type bloom"
    - fire_event: True

hit_set_period:
  cmd.run:
    - name: "ceph osd pool set swimming-cache hit_set_period 4"
    - fire_event: True

hit_set_count:
  cmd.run:
    - name: "ceph osd pool set swimming-cache hit_set_count 1200"
    - fire_event: True

# Images cannot be created on EC pools directly but will work on a 
# replicated cache
media:
  cmd.run:
    - name: "rbd -p swimming create media --size=2048"
    - unless: "rbd -p swimming ls | grep -q media$"
    - fire_event: True





