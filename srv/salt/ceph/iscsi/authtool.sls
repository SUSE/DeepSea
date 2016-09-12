
{% set keyring="/etc/ceph/ceph.client.iscsi.keyring" %}

include:
  - .keyring

add auth:
  cmd.run:
    - name: "ceph auth add client.iscsi -i {{ keyring }}"

permissions:
  cmd.run:
    - name: "chmod 644 {{ keyring }}"
