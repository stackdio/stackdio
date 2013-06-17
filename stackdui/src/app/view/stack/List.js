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

    // tbar: [
    //     {
    //         xtype: 'button',
    //         text: 'New Stack',
    //         iconCls: 'add-icon',
    //         id: 'create-stack'
    //     }
    // ],

    columns: [
        { 
            header: 'Title',
            dataIndex: 'title',
            flex: 1
        },
        { 
            header: 'Purpose',
            dataIndex: 'description',
            flex: 4
        },
        { 
            header: 'Status',
            dataIndex: 'status',
            flex: 4
        }
    ]
});


