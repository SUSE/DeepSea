# Wolffish - A SES Configuration App #

Lives in the __DeepSea__.  Aims to make short work of tough to crack iSCSI
configs.

As it grows, it might tackle bigger fish.

## Running the Wolffish app ##

### Docker ###

Based on opensuse:tumbleweed.  Will install all necessary dependencies
and serve wolffish.

    $ sudo docker build -t wolffish .
    $ sudo docker run wolffish

### Viewing Locally ###

First, make sure you have `npm4` installed.

Then, install `bower` and the `polymer-cli` globally using `npm`.

Finally:

    $ sudo npm install -g bower
    $ sudo npm install -g polymer-cli
    $ bower install
    $ polymer serve

### Building Wolffish ###

```
$ polymer build
```

This will create a `build/` folder with `bundled/` and `unbundled/` sub-folders
containing a bundled (Vulcanized) and unbundled builds, both run through HTML,
CSS, and JS optimizers.

You can serve the built versions by giving `polymer serve` a folder to serve
from:

```
$ polymer serve build/bundled
```

### Running Tests ###

Tests are currently __TODO__.

```
$ polymer test
```

Your application is already set up to be tested via
[web-component-tester](https://github.com/Polymer/web-component-tester).
Run `polymer test` to run your application's test suite locally.
