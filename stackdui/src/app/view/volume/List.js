Ext.define('stackdio.view.volume.List', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.volumeList',
    store: 'Volumes',

    autoScroll: true,

    columns: [
        { 
            header: 'Title',
            dataIndex: 'title',
            flex: 1
        },
        { 
            header: 'Description',
            dataIndex: 'description',
            flex: 2
        }
    ]
});


