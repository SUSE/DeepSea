


salt/ceph/stage/prep/step/repo/begin/{{ grains['host'] }}:
  event.send:
    - data:
        status: "prep stage begins"

include:
  - .{{ salt['pillar.get']('repo_method', 'default') }}

salt/ceph/stage/prep/step/repo/complete/{{ grains['host'] }}:
  event.send:
    - data:
        status: "prep stage complete"


