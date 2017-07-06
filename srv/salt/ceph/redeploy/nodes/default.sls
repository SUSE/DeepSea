
redeploy:
  module.run:
    - name: osd.redeploy
    - simultaneous: True

save grains:
  module.run:
    - name: osd.retain

