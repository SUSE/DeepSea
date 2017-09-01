
create mount point:
  file.directory:
    - name: {{ salt['pillar.get']('benchmark:work-directory') }}
    - user: salt
    - group: salt
    - dir_mode: 755
    - file_mode: 644
    - clean: True
    - makedirs: True

mount cephfs:
  cmd.run:
    - name: mount.ceph {{ salt['pillar.get']('mount_mon_hosts') }}:/ {{ salt['pillar.get']('benchmark:work-directory') }} -o name=deepsea_cephfs_bench,secretfile=/etc/ceph/ceph.client.deepsea_cephfs_bench.secret
  #mount.mounted:
    #- name:  {{ salt['pillar.get']('benchmark:work-directory') }}
    #- device: {{ salt['pillar.get']('mon_host')|join(',') }}:/
    #- fstype: ceph
    #- opts : name=deepsea_cephfs_bench,secretfile=/etc/ceph/ceph.client.deepsea_cephfs_bench.secret
    #- persist: False
    #- require:
      #- file: create mount point
      #- file: cephfs bench keyring

