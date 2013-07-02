Ext.define('stackdio.model.InstanceSize', {
    extend: 'Ext.data.Model'

    ,fields: [
        { name: 'id',         type: 'int' },
        { name: 'url',         type: 'string' },
        { name: 'title',         type: 'string' },
        { name: 'slug',         type: 'string' },
        { name: 'description',         type: 'string' },
        { name: 'provider_type',         type: 'string' },
        { name: 'instance_id',       type: 'string' }
    ]


    ,proxy: {
        type: 'rest',
        url: Settings.api_url + '/api/instance_sizes/',
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