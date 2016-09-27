

{% if salt['saltutil.runner']('validate.setup') == False %}
validate failed:
  salt.state:
    - name: just.exit
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - failhard: True
    - order: 1

{% endif %}


sync master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.sync

repo master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.repo
    - require:
      - salt: sync master

prepare master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.updates
    - require:
      - salt: sync master

{% set kernel= grains['kernelrelease'] | replace('-default', '')  %}

unlock:
  salt.runner:
    - name: filequeue.remove
    - queue: 'master'
    - item: 'lock'
    - unless: "rpm -q --last kernel-default | head -1 | grep -q {{ kernel }}"
    - require:
      - salt: prepare master

restart master:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.updates.{{ salt['pillar.get']('restart_method', 'restart') }}
    - require:
      - salt: unlock

#openattic:
#  salt.state:
#    - tgt: {{ salt['pillar.get']('master_minion') }}
#    - sls: ceph.openattic


complete marker:
  salt.runner:
    - name: filequeue.add
    - queue: 'master'
    - item: 'complete'
    - require:
      - salt: restart master

ready:
  salt.runner:
    - name: minions.ready
    - timeout: {{ salt['pillar.get']('ready_timeout', 300) }}
    - require:
      - salt: complete marker

include:
  - .prep.default



