{% if salt.saltutil.runner('select.minions', cluster='ceph', roles='igw') %}

add_mine_cephimages.list_function:
  salt.function:
    - name: mine.send
    - arg:
      - cephimages.list
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound

igw config:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - tgt_type: compound
    - sls: ceph.igw.config

auth:
  salt.state:
    - tgt: {{ salt['pillar.get']('master_minion') }}
    - sls: ceph.igw.auth

keyring:
  salt.state:
    - tgt: "I@roles:igw and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.igw.keyring

sysconfig:
  salt.state:
    - tgt: "I@roles:igw and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.igw.sysconfig

iscsi import:
  salt.state:
    - tgt: "{{ salt.saltutil.runner('select.one_minion', cluster='ceph', roles='igw') }}"
    - sls: ceph.igw.import

iscsi apply:
  salt.state:
    - tgt: "I@roles:igw and I@cluster:ceph"
    - tgt_type: compound
    - sls: ceph.igw

{% endif %}
# Move these to somewhere else... TBD
#multipathd:
#  salt.state:
#    - tgt: "E@client.*"
#    - tgt_type: compound
#    - sls: initiator.multipathd
#    - require:
#      - salt: iscsi apply
#
#iscsiadm:
#  salt.state:
#    - tgt: "E@client.*"
#    - tgt_type: compound
#    - sls: initiator.iscsiadm
#    - require:
#      - salt: multipathd

