{% set master = salt['master.minion']() %}

reset systemctl initially:
  salt.state:
    - tgt: {{ test_node }}
    - tgt_type: compound
    - sls: ceph.tests.restart.{{ service }}.reset

unset {{ service }} restart grain:
  module.run:
    - name: grains.setval
    - key: restart_{{ service }}
    - val: False

{#########################}
{# Check forced restarts #}

check {{ service }} forced restart:
  salt.state:
    - tgt: {{ test_node }}
    - tgt_type: compound
    - sls: ceph.tests.restart.{{ service }}.forced
    - failhard: True

{#########################}
{# Check service does not restart #}

check {{ service }} no restart:
  salt.state:
    - tgt: {{ test_node }}
    - tgt_type: compound
    - sls: ceph.tests.restart.{{ service }}.nochange
    - failhard: True

{#########################}
{# Check service restarts with change #}
change {{ service }}.conf:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.tests.restart.{{ service }}.setup

create ceph.conf:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.configuration.create

distribute ceph.conf:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.configuration

check changes:
  salt.runner:
    - name: changed.{{ service }}

check {{ service }}:
  salt.state:
    - tgt: {{ test_node }}
    - tgt_type: compound
    - sls: ceph.tests.restart.{{ service }}.change
    - failhard: True

{#########################}
{# Check service restarts with change removed #}
remove {{ service }}.conf:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.tests.restart.{{ service }}.teardown

reset systemctl:
  salt.state:
    - tgt: {{ test_node }}
    - tgt_type: compound
    - sls: ceph.tests.restart.{{ service }}.reset

reset ceph.conf:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.configuration.create

redistribute ceph.conf:
  salt.state:
    - tgt: {{ master }}
    - tgt_type: compound
    - sls: ceph.configuration

check changes again:
  salt.runner:
    - name: changed.{{ service }}

check {{ service }} again:
  salt.state:
    - tgt: {{ test_node }}
    - tgt_type: compound
    - sls: ceph.tests.restart.{{ service }}.change

