
prevent empty rendering:
  test.nop:
    - name: skip

{% set keyring_file = "/srv/salt/ceph/openattic/cache/ceph.client.openattic.keyring" %}

auth {{ keyring_file }}:
  cmd.run:
    - name: "ceph auth add client.openattic -i {{ keyring_file }}"


