Ext.define('stackdio.model.Volume', {
    extend: 'Ext.data.Model'

    ,fields: [
        { name: 'id',               type: 'int' },
        { name: 'title',            type: 'string' }
    ]


    ,proxy: {
        type: 'rest',
        url: 'http://localhost:8000/api/volumes/',
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