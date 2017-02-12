
switch kernel:
  module.run:
    - name: kernel.replace
    - kwargs:
        os: 
          SUSE: 
            kernel: kernel-default
            candidates:
            - kernel-default-base
      

update packages:
  module.run:
    - name: pkg.upgrade



