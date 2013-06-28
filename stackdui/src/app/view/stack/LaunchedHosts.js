Ext.define('stackdio.view.stack.LaunchedHosts', {
    extend: 'Ext.grid.Panel',
    alias: 'widget.launchedStackHosts',
    

    autoScroll: true,
    store: 'LaunchedHosts',
    anchor: '100% 30%',
    padding: '10',
    stripeRows: true,
    columns: [
        {
            header: 'Hostname',
            dataIndex: 'hostname',
            flex: 2
        },
        {
            header: 'DNS Name',
            dataIndex: 'ec2_metadata.dnsName',
            flex: 4,
            renderer: function (id, metaData, record, rowIndex, colIndex, store, view) {
                return record.data.ec2_metadata.dnsName
            }
        },
        {
            header: 'Public IP',
            dataIndex: 'ec2_metadata.public_ips',
            flex: 2,
            renderer: function (id, metaData, record, rowIndex, colIndex, store, view) {
                return record.data.ec2_metadata.public_ips
            }
        },
        {
            header: 'State',
            dataIndex: 'ec2_metadata.state',
            flex: 1,
            renderer: function (id, metaData, record, rowIndex, colIndex, store, view) {
                return record.data.ec2_metadata.state
            }
        },
        {
            xtype: 'actioncolumn',
            width: 25,
            items: [{
                icon: '/static/img/icons/delete.png',  // Use a URL in the icon config
                tooltip: 'Delete',
                handler: function (grid, rowIndex, colIndex) {

                }
            }]
        }
    ]
});
