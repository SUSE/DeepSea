
hwinfo repo:
  pkgrepo.managed:
    - name: centos-nux-dextop-repo
    - humanname: CentoOS-$releasever - Nux Dextop
    - baseurl: http://li.nux.ro/download/nux/dextop/el$releasever/$basearch/
    - gpgcheck: False
    - enabled: True
    - fire_event: True

stage prep dependencies:
  pkg.installed:
    - pkgs:
      - lsscsi
      - pciutils
      - gdisk
      - python3-boto
      - python3-rados
      - iperf3
      - lshw
      - hwinfo
      - python-netaddr
      - jq
    - fire_event: True
    - refresh: True

