{% set os = salt['grains.get']('os') %}

{% if os == 'SUSE' %}

stage prep dependencies suse:
  pkg.installed:
    - pkgs:
      - lsscsi
      - pciutils
      - gptfdisk
      - python-boto
      - iperf
    - fire_event: True

{% elif os == 'Ubuntu' %}

stage prep dependencies ubuntu:
  pkg.installed:
    - pkgs:
      - lsscsi
      - pciutils
      - gdisk
      - python-boto
      - iperf
    - fire_event: True

{% else %}

nop:
  test.nop

{% endif %}
