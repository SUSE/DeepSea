

open-iscsi:
  pkg.installed:
    - pkgs:
      - open-iscsi

#open-iscsi:
#  cmd.run:
#    - name: "zypper --non-interactive --no-gpg-checks in open-iscsi"

iscsid:
  service.running:
    - name: iscsid

discover:
  cmd.run:
    - name: "iscsiadm -m discovery -t st -p igw1"
    - shell: /bin/bash
    - unless: "iscsiadm -m node | grep -q 'iqn'"

login:
  cmd.run:
    - name: "iscsiadm -m node -L all"
    - shell: /bin/bash
    - unless: "multipath -ll | grep -q '\n'"
    - require:
      - cmd: discover

