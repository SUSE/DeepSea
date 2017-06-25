
prevent empty rendering:
  test.nop:
    - name: skip

{% set keyring_file = salt['keyring.file']('osd') %}
auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add client.bootstrap-osd -i {{ keyring_file }}"

{% set keyring_file = "/srv/salt/ceph/osd/cache/ceph.client.storage.keyring" %}
auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add client.storage -i {{ keyring_file }}"


