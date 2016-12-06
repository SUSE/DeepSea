
/etc/ganesha/ganesha.conf:
  file.rename:
  - name: /etc/ganesha/ganesha.conf.orig
  - source: /etc/ganesha/ganesha.conf

/etc/ganesha/ceph.conf:
  file.symlink:
  - name: /etc/ganesha/ganesha.conf
  - target: /etc/ganesha/ceph.conf
  - force: True
