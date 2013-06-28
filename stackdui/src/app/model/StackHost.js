Ext.define('stackdio.model.StackHost', {
    extend: 'Ext.data.Model'

    ,fields: [
        { name: 'fqdn',           type: 'string' },
        { name: 'created',        type: 'date' },
        { name: 'provider_dns',   type: 'string' },
        { name: 'state',          type: 'string' },
        { name: 'hostname',       type: 'string' },
        { name: 'status',         type: 'string' },
        { name: 'status_detail',  type: 'string' },
        { name: 'url',            type: 'string' },
        { name: 'ec2_metadata',   type: 'auto'   }
    ]
});