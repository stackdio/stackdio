Ext.define('stackdio.model.HostVolume', {
    extend: 'Ext.data.Model'

    ,fields: [
        { name: 'id',            type: 'int' },
        { name: 'title',         type: 'string' },
        { name: 'name',          type: 'string' },
        { name: 'mount_point',   type: 'string' }
    ]


    ,proxy: {
        type: 'rest',
        url: Settings.api_url + '/api/volumes/',
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