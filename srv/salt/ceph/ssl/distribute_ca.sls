/etc/pki/trust/anchors/deepsea_ca_cert.crt:
  file.managed:
    - source: salt://ceph/ssl/cache/deepsea_ca_cert.crt
    - user: root
    - group: root
    - mode: 644
    - fire_event: True

update ca certificates:
  cmd.run:
    - name: update-ca-certificates
    - fire_event: True
