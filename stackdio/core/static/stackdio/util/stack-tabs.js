define(['util/galaxy'], funtion($galaxy) {
    return {
        goToDetail: function(stack) {
            $galaxy.transport({
                location: 'stack.detail',
                payload: {
                    stack: stack.id
                }
            }); 
        },
        goToHosts: function(stack) {
            $galaxy.transport({
                location: 'stack.hosts',
                payload: {
                    stack: stack.id
                }
            }); 
        },
        goToLogs: function(stack) {
            $galaxy.transport({
                location: 'stack.hosts',
                payload: {
                    stack: stack.id
                }
            }); 
        },
        goToAccessRules: function(stack) {
            $galaxy.transport({
                location: 'stack.detail',
                payload: {
                    stack: stack.id
                }
            }); 
        },
        goToActions: function(stack) {
            $galaxy.transport({
                location: 'stack.detail',
                payload: {
                    stack: stack.id
                }
            }); 
        }
    };
});
