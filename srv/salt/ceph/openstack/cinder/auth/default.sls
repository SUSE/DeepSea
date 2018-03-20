{% set keyring_file = salt['keyring.file']('cinder') %}

auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add client.cinder -i {{ keyring_file }}"

