set noout:
  cmd.run:
    - name: "/usr/bin/ceph osd set noout"

warning:
  module.run:
    - name: advise.generic
    - message: "Ceph will be set to noout during the upgrade process to avoid unnecessary data shuffling. Make sure it's disabled afterwards with `ceph osd unset noout`"
