
backstore:
  cmd.run:
    - name: "rbd -p rbd create archive --size=1024"
    - unless: "rbd -p rbd ls | grep -q archive$"

archive1:
  cmd.run:
    - name: "rbd -p rbd create archive1 --size=768"
    - unless: "rbd -p rbd ls | grep -q archive1$"

archive2:
  cmd.run:
    - name: "rbd -p rbd create archive2 --size=512"
    - unless: "rbd -p rbd ls | grep -q archive2$"

erasure profile:
  cmd.run:
    - name: "ceph osd erasure-code-profile set three-one k=3 m=1"
    - unless: "ceph osd erasure-code-profiles ls | grep -q three-one"

swimming:
  cmd.run:
    - name: "ceph osd pool create swimming 128 erasure three-one"
    - unless: "ceph osd pool ls | grep -q swimming$"

media:
  cmd.run:
    - name: "rbd -p swimming create media --size=2048"
    - unless: "rbd -p swimming ls | grep -q media$"

cache:
  cmd.run:
    - name: "ceph osd pool create swimming-cache 256 256"
    - unless: "ceph osd pool ls | grep -q swimming-cache"

cache tier:
  cmd.run:
    - name: "ceph osd tier add swimming swimming-cache"

cache mode:
  cmd.run:
    - name: "ceph osd tier cache-mode swimming-cache writeback"

overlay:
  cmd.run:
    - name: "ceph osd tier set-overlay swimming swimming-cache"

hit_set_type:
  cmd.run:
    - name: "ceph osd pool set swimming-cache hit_set_type bloom"

hit_set_period:
  cmd.run:
    - name: "ceph osd pool set swimming-cache hit_set_period 4"

hit_set_count:
  cmd.run:
    - name: "ceph osd pool set swimming-cache hit_set_count 1200"







