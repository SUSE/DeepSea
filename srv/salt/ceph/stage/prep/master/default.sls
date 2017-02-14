

{% if salt['saltutil.runner']('validate.setup') == False %}
validate failed:
  salt.state:
    - name: just.exit
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True

{% endif %}

sync master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.sync

{% set notice = salt['saltutil.runner']('advise.salt_run') %}

repo master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.repo

{% set kernel_not_installed = salt['saltutil.runner'](
                'kernel.verify_kernel_installed',
                kernel_package='kernel-default',
                target_id=salt['pillar.get']('master_minion'))|length > 0
%}
{% set change_kernel = salt['environ.get']('CHANGE_KERNEL') %}

prepare master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.updates
{% if kernel_not_installed %}
    - pillar: { "change_kernel": "{{ change_kernel }}", "kernel_package": "kernel-default" }
{% endif %}

{% set kernel= grains['kernelrelease'] | replace('-default', '')  %}

unlock:
  salt.runner:
    - name: filequeue.remove
    - queue: 'master'
    - item: 'lock'
    - unless: "rpm -q --last kernel-default | head -1 | grep -q {{ kernel }}"

restart master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.updates.restart

#openattic:
#  salt.state:
#    - tgt: {{ salt['pillar.get']('master_minion') }}
#    - sls: ceph.openattic


complete marker:
  salt.runner:
    - name: filequeue.add
    - queue: 'master'
    - item: 'complete'

ready:
  salt.runner:
    - name: minions.ready
    - timeout: {{ salt['pillar.get']('ready_timeout', 300) }}




