{% set keyring_file = salt['keyring.file']('cinder-backup') %}

auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add client.cinder-backup -i {{ keyring_file }}"

