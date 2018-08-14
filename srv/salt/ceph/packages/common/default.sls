{% set os = salt['grains.get']('os') %}

{% if grains.get('osfullname', '') == 'SLES' %}

install ses-realease package:
  pkg.installed:
    - pkgs:
      - ses-release

{% endif %}

{% if os == 'SUSE' %}

stage prep dependencies suse:
  pkg.installed:
    - pkgs:
      - lsscsi
      - smartmontools
      - pciutils
      - gptfdisk
      - python3-boto
      - python3-rados
      - iperf
      - lsof
      - jq
      - tuned
      - libgio-2_0-0
      - polkit
    - fire_event: True
    - refresh: True

{% elif os == 'Ubuntu' %}

stage prep dependencies ubuntu:
  pkg.installed:
    - pkgs:
      - lsscsi
      - smartmontools
      - pciutils
      - gdisk
      - python3-boto
      - python3-rados
      - iperf
      - jq
    - fire_event: True
    - refresh: True

{% elif os == 'CentOS' %}

hwinfo repo for CentOS:
  pkgrepo.managed:
    - name: centos-nux-dextop-repo
    - humanname: CentoOS-$releasever - Nux Dextop
    - baseurl: http://li.nux.ro/download/nux/dextop/el$releasever/$basearch/
    - gpgcheck: False
    - enabled: True
    - fire_event: True

stage prep dependencies CentOS:
  pkg.installed:
    - pkgs:
      - lsscsi
      - smartmontools
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

{% else %}

nop:
  test.nop

{% endif %}
