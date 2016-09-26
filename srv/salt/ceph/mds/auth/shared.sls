
{% set client = "mds.mds" %}
{% set keyring_file = salt['keyring.file']('mds', 'mds')  %}

auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add {{ client }} -i {{ keyring_file }}"



