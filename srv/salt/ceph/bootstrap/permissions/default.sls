# we need to change this to salt:salt for the master to read the files
change bootstrap dir ownership:
  file.directory:
    - names:
        - /srv/salt/ceph/bootstrap
    - user: salt
    - group: salt
    - makedirs: true
    - recurse:
        - user
        - group
