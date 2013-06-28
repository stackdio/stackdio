Ext.define('stackdio.model.AccountProfile', {
    extend: 'Ext.data.Model'

    ,fields: [
        { name: 'id',                     type: 'int' },
        { name: 'title',                  type: 'string' },
        { name: 'slug',                   type: 'string' },
        { name: 'description',            type: 'string' },
        { name: 'cloud_provider',         type: 'int' },
        { name: 'image_id',               type: 'string' },
        { name: 'default_instance_size',  type: 'int' },
        { name: 'script',                 type: 'string' },
        { name: 'ssh_user',               type: 'string' }
    ]

    ,proxy: {
        type: 'rest',
        url: '/api/profiles/',
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