
{% set keyring_file = salt['keyring.file']('igw', 'client.igw')  %}

auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add client.igw -i {{ keyring_file }}"

