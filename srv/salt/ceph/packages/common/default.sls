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
      - pciutils
      - gptfdisk
      - python-boto
      - python-rados
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
      - pciutils
      - gdisk
      - python-boto
      - python-rados
      - iperf
      - jq
    - fire_event: True
    - refresh: True

{% else %}

nop:
  test.nop

{% endif %}
