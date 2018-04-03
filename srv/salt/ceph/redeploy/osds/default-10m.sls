
redeploy:
  module.run:
    - name: osd.redeploy
    - kwargs:
        timeout: 600
        delay: 12

save grains:
  module.run:
    - name: osd.retain

