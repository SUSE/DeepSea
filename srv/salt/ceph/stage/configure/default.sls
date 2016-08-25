

#policy:
#  salt.state:
#    - tgt: {{ salt['pillar.get']('master_minion') }}
#    - sls: file.exists

push proposals:
  salt.runner:
    - name: push.proposal


refresh_pillar1:
  salt.state:
    - tgt: '*'
    - sls: ceph.refresh
    - require:
      - salt: push proposals

post configuration:
  salt.runner:
    - name: configure.cluster
    - require: 
      - salt: refresh_pillar1

refresh_pillar2:
  salt.state:
    - tgt: '*'
    - sls: ceph.refresh
    - require: 
      - salt: post configuration



