
redeploy:
  module.run:
    - name: osd.redeploy
    - simultaneous: True
    - kwargs:
        timeout: 600
        delay: 12

save grains:
  module.run:
    - name: osd.retain

