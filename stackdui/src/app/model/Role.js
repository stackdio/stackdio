Ext.define('stackdio.model.Role', {
    extend: 'Ext.data.Model'

    ,fields: [
         { name: 'id',          type: 'int' }
        ,{ name: 'title',       type: 'string' }
        ,{ name: 'role_name',   type: 'string' }
    ]

    ,proxy: {
        type: 'rest',
        url: Settings.api_url + '/api/roles/',
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