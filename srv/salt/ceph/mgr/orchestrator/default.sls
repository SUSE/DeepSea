ceph mgr module enable deepsea:
  cmd.run:
  - failhard: True

ceph orchestrator set backend deepsea:
  cmd.run:
  - failhard: True

ceph deepsea config-set salt_api_url "{{ salt['pillar.get']('salt_api_url') }}":
  cmd.run:
  - failhard: True

ceph deepsea config-set salt_api_username "{{ salt['pillar.get']('salt_api_username') }}":
  cmd.run:
  - failhard: True

ceph deepsea config-set salt_api_password "{{ salt['pillar.get']('salt_api_password') }}":
  cmd.run:
  - failhard: True

