
check lock:
  module.run:
    - name: zypper.ready
    - fire_event: True

ceph install:
  cmd.run:
    - name: "zypper --non-interactive --no-gpg-checks in ceph"
    - require:
      - module: check lock
    - fire_event: True
