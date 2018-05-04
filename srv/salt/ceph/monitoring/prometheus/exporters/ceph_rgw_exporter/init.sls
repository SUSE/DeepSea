
{% set custom = salt['pillar.get']('monitoring_prometheus_exporters_ceph_rgw_exporter', 'not a file') %}
{% from 'ceph/macros/os_switch.sls' import os_switch with context %}

include:
  - .{{ os_switch(custom) }}
