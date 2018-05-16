
{% from 'ceph/macros/os_switch.sls' import os_switch with context %}
{% set os_grain = salt['grains.get']('os') %}
{% set foo = salt['grains.set']('os', 'file') %}

{% if os_switch('no custom') == 'file' %}

succees file:
  test.succeed_without_changes:
    - name: file success

{% else %}

fail file:
  test.fail_without_changes:
    - name: file failure {{ os_switch('no custom') }}

{% endif %}

{% if os_switch('custom') == 'custom' %}

succees custom:
  test.succeed_without_changes:
    - name: custom success

{% else %}

fail custom:
  test.fail_without_changes:
    - name: custom failure {{ os_switch('custom') }}

{% endif %}

reset os grain {{ os_grain }}:
  module.run:
    - name: grains.setval
    - key: os
    - val: {{ os_grain }}

