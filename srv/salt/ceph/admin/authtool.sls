
admin keyring:
  cmd.run:
    - name: ceph-authtool /etc/ceph/ceph.client.admin.keyring  --create-keyring --name=client.admin --add-key={{ salt['pillar.get']('keyring:admin') }} --cap mon 'allow *' --cap mds 'allow *' --cap osd 'allow *'
    - fire_event: True
