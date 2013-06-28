Ext.define('stackdio.view.snapshot.List', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.snapshotList',
    store: 'Snapshots',

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


