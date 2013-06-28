Ext.define('stackdio.model.Host', {
    extend: 'Ext.data.Model'

    ,fields: [
        { name: 'id',               type: 'int' },
        { name: 'stack',            type: 'string' },
        { name: 'count',            type: 'int' },
        { name: 'cloud_profile',    type: 'int' },
        { name: 'instance_size',    type: 'int' },
        { name: 'roles',            type: 'auto' },
        { name: 'hostname',         type: 'string' },
        { name: 'security_groups',  type: 'string' }
    ]


    ,proxy: {
        type: 'rest',
        url: '/api/hosts/',
        reader: {
            type: 'json',
            root: 'results'
        },
        headers: {
            "Authorization": "Basic " + Base64.encode('testuser:password')
        },
        pageParam: undefined,
        limitParam: undefined,
        startParam: undefined
    }
});