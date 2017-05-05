// -----------------------------------------------------------------------------
// salt-events.html
//
// A simple element that taps into salt-api's events bus.  Utilizes the EventSource
// API which does not run on all browsers.
// -----------------------------------------------------------------------------

// EventSource constants.
const ES_CONNECTING = 0;
const ES_OPEN = 1;
const ES_CLOSED = 2;

Polymer({
    is: 'salt-events',

    properties: {
        saltApiNode: {
            type: String
        },
        saltApiPort: {
            type: Number
        },
        saltApiSsl: {
            type: Boolean,
            value: false
        },
        saltEventsUrl: {
            type: String
        },

        evSrc: {
            type: Object
        },

        evOnSaltEvMsg: {
            type: String,
            value: "salt-events-msg"
        },
        evOnSaltEvOpen: {
            type: String,
            value: "salt-events-open"
        },
        evOnSaltEvClose: {
            type: String,
            value: "salt-events-close"
        },
        evOnSaltEvErr: {
            type: String,
            value: "salt-events-err"
        }
    },

    ready: function() {
        console.log(this.is + ": ready()");
    },

    // Fires the desired evStr event.
    _fire: function(evStr, data) {
        console.log(this.is + ": firing '" + evStr + "' event.");
        this.fire(evStr, data);
    },

    // EventSource.onopen() callback.
    onOpen: function() {
        console.info(this.is + ": Listening for salt events.");
        this._fire(this.evOnSaltEvOpen, null);
    },

    // EventSource.onerror() callback.
    onErr: function(err) {
        console.error(this.is + ": encountered error.");
        console.error(err);
        this._fire(this.evOnSaltEvErr, err);
    },

    // EventSource.onmessage() callback.
    onMsg: function(msg) {
        var saltEvent = JSON.parse(msg.data);
        console.log(this.is + ": received " + JSON.stringify(saltEvent));
        this._fire(this.evOnSaltEvMsg, saltEvent);
    },

    // Closes the EventSource instance connected to the salt events bus.
    close: function() {
        console.log(this.is + ": close()");

        if (this.evSrc && this.evSrc.readyState !== ES_CLOSED) {
            console.log(this.is + ": Closing existing EventSource instance.");
            this.evSrc.close();
            this._fire(this.evOnSaltEvClose);
        }
    },

    // Retain salt-api node, port and whether ssl should be used.
    _saveSaltApiUrlComponents(saltApiNode, saltApiPort, ssl) {
        this.saltApiNode = saltApiNode;
        this.saltApiPort = saltApiPort;
        this.saltApiSsl = ssl;
    },

    // Generates and returns salt-api/events url based on saved url components.
    _genSaltEventsUrl: function() {
        var protocol = this.saltApiSsl ? "https://" : "http://";

        return protocol + this.saltApiNode + ":" + this.saltApiPort + "/events";
    },

    // connect() helper function.  Performs the actual EventSource instantiation and
    // sets the various EventSource handler functions.
    _connect: function() {
        console.log(this.is + ": _connect()");

        // Check for existing EventSource instance and first close.
        this.close();

        this.evSrc = new EventSource(this.saltEventsUrl, { withCredentials: true });
        this.evSrc.onopen = this.onOpen.bind(this);
        this.evSrc.onerror = this.onErr.bind(this);
        this.evSrc.onmessage = this.onMsg.bind(this);
    },

    // Connect <salt-events> to the salt events bus.  Checks if a connection/re-connection
    // is necessary based on changes to the salt event bus url as well as the current state
    // of an existing EventSource instance.
    connect: function(saltApiNode, saltApiPort, ssl) {
        var connectNeeded = false;
        var saltEventsUrl = "";

        console.log(this.is + ": connect()");

        this._saveSaltApiUrlComponents(saltApiNode, saltApiPort, ssl);

        // Determine if we're not already connected to the appropriate salt event bus.
        saltEventsUrl = this._genSaltEventsUrl();
        connectNeeded = (saltEventsUrl !== this.saltEventsUrl) || connectNeeded ? true : false;
        connectNeeded = (this.evSrc && (this.evSrc.readyState !== ES_OPEN && this.evSrc.readyState !== ES_CONNECTING)) || connectNeeded ? true : false;

        // If we've updated the salt events bus url, save it.
        if (this.saltEventsUrl !== saltEventsUrl) {
            this.saltEventsUrl = saltEventsUrl;
        }

        // Connect if needed.
        if (connectNeeded) {
            this._connect();
        }
    }
});
