{% if grains.get('os', '') == 'CentOS' %}

install_ganesha_repo:
  pkgrepo.managed:
    - name: nfs-ganesha-repo
    - humanname: NFS Ganesha repo
    - baseurl: http://download.ceph.com/nfs-ganesha/rpm-V2.5-stable/luminous/$basearch/
    - gpgcheck: False
    - enabled: True
    - fire_event: True

{% endif %}

install_ganesha:
  pkg.installed:
    - pkgs:
        - nfs-ganesha
        - nfs-ganesha-ceph
        - nfs-ganesha-rgw
    - fire_event: True
