// -----------------------------------------------------------------------------
// rgw-token.js
//
// Grab an RGW token from DeepSea.  Underneath, DS uses `radosgw-token`.
// -----------------------------------------------------------------------------
Polymer({
    is: 'rgw-token',

    properties: {
        tokenTypes: {
            type: Array,
            value: ["ldap", "ad"]
        },
        tokenType: {
            type: String,
            value: "ldap"
        },
        accessKey: {
            type: String
        },
        secretAccessKey: {
            type: String
        },
        getTokenButtonDisabled: {
            type: Boolean,
            value: false
        },
        token: {
            type: String,
        }
    },

    listeners: {
	"wf-salt-api-response": "handleToken200",
	"wf-salt-api-error": "handleTokenErr"
    },

    ready: function() {
        console.log(this.is + ": ready()");
    },

    handleToken200: function(e) {
        console.log(this.is + ":" + arguments.callee.name + ": caught " + e.type);
        var resp = e.detail.response.return[0];

        // Just take the first one.
        Object.keys(resp).forEach(function(key,index) {
            if (index === 0 && resp[key]) {
                this.token = resp[key];
            }
        }, this);

        if (this.token) {
            console.log(this.is + ": received token: " + this.token);
        } else {
            console.error(this.is + ": received empty token");
        }

        this.getTokenButtonDisabled = false;
    },

    handleTokenErr: function(e) {
        console.log(this.is + ":" + arguments.callee.name + ": caught " + e.type);
        console.error(this.is + ": Failed to obtain RGW token");
        alert("Failed to obtain RGW token");

        this.getTokenButtonDisabled = false;
    },

    setTokenType: function(e) {
        var tokenType = e.model.__data__.t;
        this.tokenType = tokenType
    },

    getToken: function() {
        var dataDict = {
            ttype: this.tokenType,
            access: this.accessKey,
            secret: this.secretAccessKey
        };

        this.getTokenButtonDisabled = true;
        this.$.gettoken.data = dataDict;
        this.$.gettoken.runPost();
    },

    clearToken: function() {
        this.token = "";
    }
});
