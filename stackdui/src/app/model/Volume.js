Ext.define('stackdio.model.Volume', {
    extend: 'Ext.data.Model'

    ,fields: [
         { name: 'id',              type: 'int' }
        ,{ name: 'snapshot',        type: 'string' }
        ,{ name: 'device',          type: 'string' }
        ,{ name: 'mount_point',     type: 'string' }
    ]
});