Ext.define('stackdio.model.Stack', {
    extend: 'Ext.data.Model'

    ,fields: [
        { name: 'title',         type: 'string' },
        { name: 'description',         type: 'string' },
        { name: 'url',         type: 'string' },
        { name: 'user',         type: 'string' },
        { name: 'hosts',         type: 'string' },
        { name: 'created',         type: 'string' },
        { name: 'status',         type: 'string' },
        { name: 'status_detail',         type: 'string' }
    ]

    ,proxy: {
        type: 'rest',
        url: Settings.api_url + '/api/stacks/',
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