

{% set keyring_file = salt['keyring.file']('osd') %}
auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add client.bootstrap-osd -i {{ keyring_file }}"


