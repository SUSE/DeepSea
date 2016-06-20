
load modules:
  module.run:
    - name: saltutil.sync_all
    - refresh: True

sync time:
  cmd.run:
    - name: "sntp -S -c salt"
