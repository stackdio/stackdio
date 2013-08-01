Ext.define('stackdio.store.ProviderAccounts', {
    extend: 'Ext.data.Store'
    ,model: 'stackdio.model.ProviderAccount'
    ,autoLoad: true

    ,groupers: [
        {
            property : 'provider_type_name',
            direction: 'ASC'
        }
    ]
});