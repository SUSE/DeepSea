
load modules:
  module.run:
    - name: saltutil.sync_all
    - refresh: True

include:
  - .{{ salt['pillar.get']('time_service') }}

