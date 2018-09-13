# Baseline engulf test runs against a deployed cluster, engulfing itself, then:
#
# - recursively diff profile-default against profile-import
# - verify the generated policy.cfg has the same *effect* as the original
#   one, if not necessarily the same form (the engulf won't generate wildcard
#   names, and roles might be assigned in a different order).
#

{% set master = salt['master.minion']() %}

backup default proposal:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.tests.engulf.proposal-backup

save pillar data:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.tests.engulf.pillar-save

engulf:
  salt.runner:
    - name: populate.engulf_existing_cluster
    - failhard: True
    - exception: True

verify storage profiles:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.tests.engulf.profile-verify

push engulfed proposal:
  salt.runner:
    - name: push.proposal

refresh_pillar1:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.refresh

verify pillar data:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.tests.engulf.pillar-verify

restore default proposal:
  salt.state:
    - tgt: {{ master }}
    - sls: ceph.tests.engulf.proposal-restore

push default proposal:
  salt.runner:
    - name: push.proposal

refresh_pillar2:
  salt.state:
    - tgt: '{{ salt['pillar.get']('deepsea_minions') }}'
    - tgt_type: compound
    - sls: ceph.refresh
