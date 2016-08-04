
{% set keyring="/srv/salt/ceph/iscsi/files/ceph.client.iscsi.keyring" %}

iscsi keyring:
  cmd.run:
    - name: "ceph-authtool -C -n client.iscsi --gen-key {{ keyring }} --cap osd 'allow rwx' --cap mon 'allow rx'"
    - unless: "stat {{ keyring }}" 

add auth:
  cmd.run:
    - name: "ceph auth add client.iscsi -i {{ keyring }}"

permissions:
  cmd.run:
    - name: "chmod 644 {{ keyring }}"
