Ext.define('stackdio.model.ProviderType', {
    extend: 'Ext.data.Model'

    ,fields: [
        { name: 'url',         type: 'string' },
        { name: 'type_name',   type: 'string' },
        { name: 'title',       type: 'string' }
    ]

    ,proxy: {
        type: 'rest',
        url: 'http://localhost:8000/api/provider_types/',
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