Ext.define('stackdio.model.ProfileScript', {
    extend: 'Ext.data.Model'

    ,fields: [
        { name: 'os',         type: 'string' },
        { name: 'script',       type: 'string' }
    ]

    ,proxy: {
        type: 'rest',
        url: 'http://localhost:8000/api/profile_scripts/',
        reader: {
            type: 'json'
        },
        headers: {
            "Authorization": "Basic " + Base64.encode('testuser:password')
        },
        pageParam: undefined,
        limitParam: undefined,
        startParam: undefined
    }
});