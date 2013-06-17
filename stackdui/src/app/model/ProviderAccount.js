Ext.define('stackdio.model.ProviderAccount', {
    extend: 'Ext.data.Model'

    ,fields: [
        { name: 'id',         type: 'int' },
        { name: 'title',         type: 'string' },
        { name: 'description',         type: 'string' },
        { name: 'slug',         type: 'string' },
        { name: 'provider_type',         type: 'string' },
        { name: 'provider_type_name',         type: 'string' },
        { name: 'yaml',       type: 'string' }
    ]

    ,proxy: {
        type: 'rest',
        url: 'http://localhost:8000/api/providers/',
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