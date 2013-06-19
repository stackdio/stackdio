Ext.define('stackdio.view.stack.List', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.stackList',
    store: 'Stacks',

    autoScroll: true,
    features: [{
        id:             'typeGrouping',
        ftype:          'grouping',
        groupHeaderTpl: 'Status: {status}',
        startCollapsed: true
    }],

    columns: [
        { 
            header: 'Title',
            dataIndex: 'title',
            flex: 1
        },
        { 
            header: 'Purpose',
            dataIndex: 'description',
            flex: 3
        },
        { 
            header: 'Status',
            dataIndex: 'status',
            flex: 1
        }
    ]
});


