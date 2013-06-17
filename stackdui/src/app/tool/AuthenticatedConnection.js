Ext.define('stackdio.tool.AuthenticatedConnection', {
    extend: 'Ext.data.Connection',
    alias: 'widget.apiRequest',

    request: function (options) {
        if (!options.hasOwnProperty('headers')) options.headers = {};
        options.headers['Authorization'] = "Basic " + Base64.encode('testuser:password');
        options.headers['Accept'] = 'application/json';
        this.callParent([options]);
    },

    constructor : function (config) {
        this.callParent(config);

        this.on("beforerequest", function(){
            // Leaving this here for reference
        });

        this.on("requestcomplete", function(ajax, response){
            // Leaving this here for reference
        });
    }
});