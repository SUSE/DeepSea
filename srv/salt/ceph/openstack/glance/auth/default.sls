{% set keyring_file = salt['keyring.file']('glance') %}

auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add client.glance -i {{ keyring_file }}"

