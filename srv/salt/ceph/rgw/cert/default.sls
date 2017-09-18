# Create a cert in pem format and copy this to /srv/salt/ceph/rgw/cert/rgw.pem
deploy the rgw.pem file:
  file.managed:
    - name: /etc/ceph/rgw.pem
    - source: salt://ceph/rgw/cert/rgw.pem
    - user: ceph
    - group: ceph
    - mode: 600
