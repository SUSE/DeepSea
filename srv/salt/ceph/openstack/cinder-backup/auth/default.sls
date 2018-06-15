{% set prefix = pillar['openstack_prefix'] + "-" if 'openstack_prefix' in pillar else "" %}
{% set keyring_file = salt['keyring.file']('cinder-backup', prefix) %}

auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add client.{{ prefix }}cinder-backup -i {{ keyring_file }}"

