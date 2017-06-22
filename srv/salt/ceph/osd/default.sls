
include:
  - .keyring

deploy OSDs:
  module.run:
    - name: osd.deploy

save grains:
  module.run:
    - name: osd.retain

verify OSDs:
  module.run:
    - name: osd.report
    - failhard: True
