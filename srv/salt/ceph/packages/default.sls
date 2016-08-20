
check lock:
  module.run:
    - name: zypper.ready

ceph install:
  cmd.run:
    - name: "zypper --non-interactive --no-gpg-checks in ceph"
    - require:
      - module: check lock
