
stop nfs-ganesha:
  service.dead:
    - name: nfs-ganesha
    - enable: False
    - onlyif: "test -f /usr/bin/ganesha.nfsd"

