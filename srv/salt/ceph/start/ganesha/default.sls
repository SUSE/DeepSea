
start nfs-ganesha:
  service.running:
    - name: nfs-ganesha
    - onlyif: "test -f /usr/bin/ganesha.nfsd"

