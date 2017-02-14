
begin:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.events.begin_prep

sync:
  salt.state:
    - tgt: '*'
    - sls: ceph.sync

mines:
  salt.state:
    - tgt: '*'
    - sls: ceph.mines

repo:
  salt.state:
    - tgt: '*'
    - sls: ceph.repo

common packages:
  salt.state:
    - tgt: '*'
    - sls: ceph.packages.common

{% set kernel_not_installed = salt['saltutil.runner'](
                'kernel.verify_kernel_installed',
                kernel_package='kernel-default',
                target_id='*')|length > 0
%}
{% set change_kernel = salt['environ.get']('CHANGE_KERNEL') %}
updates:
  salt.state:
    - tgt: '*'
    - sls: ceph.updates
{% if kernel_not_installed %}
    - pillar: { "change_kernel": "{{ change_kernel }}", "kernel_package": "kernel-default" }
{% endif %}

restart:
  salt.state:
    - tgt: '*'
    - sls: ceph.updates.restart

complete:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.events.complete_prep

