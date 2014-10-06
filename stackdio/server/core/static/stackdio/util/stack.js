define(['util/galaxy', 'util/alerts', 'store/Stacks', 'bootbox'], function($galaxy, alerts, StackStore, bootbox) {
    return {
        getStatusType: function(status) {
            switch(status) {
                case 'pending':
                    return 'info';

                case 'launching':
                case 'configuring':
                case 'syncing':
                case 'provisioning':
                case 'orchestrating':
                case 'finalizing':

                case 'destroying':

                case 'starting':
                case 'stopping':
                case 'terminating':
                case 'executing_action':
                    return 'warning';

                case 'error':
                    return 'danger';

                case 'finished':
                    return 'success';

                default:
                    return 'default';
            }
	    },
	    // This builds the HTML for the stack history popover element
        popoverBuilder: function (stack) {
            return stack.fullHistory.map(function (h) {
                var content = [];

                content.push("<div class=\'dotted-border xxsmall-padding\'>");
                content.push("<div");
                if (h.level === 'ERROR') {
                    content.push(" class='btn-danger'");

                }
                content.push('>');
                content.push(h.status_detail);
                content.push('</div>');
                content.push("<div class='grey'>");
                content.push(moment(h.created).fromNow());
                content.push('</div>');
                content.push('</div>');

                return content.join('');

            }).join('');
        },
        showStackDetails: function (stack) {
            $galaxy.transport({
                location: 'stack.detail',
                payload: {
                    stack: stack.id
                }
            });
        },
        doStackAction: function (action, evt, stack) {
            var data = JSON.stringify({
                action: action.toLowerCase()
            });

            /*
             *  Unless the user wants to delete the stack permanently (see below)
             *  then just PUT to the API with the appropriate action.
             */
            if (action !== 'Delete') {
                bootbox.confirm("<h4>"+action+" stack '"+stack.title+"'</h4><br />Please confirm that you want to perform this action on the stack.", function (result) {
                    if (result) {
                        $.ajax({
                            url: stack.action,
                            type: 'POST',
                            data: data,
                            headers: {
                                "X-CSRFToken": stackdio.settings.csrftoken,
                                "Accept": "application/json",
                                "Content-Type": "application/json"
                            },
                            success: function (response) {
                                alerts.showMessage('#success', 'Stack ' + action.toLowerCase() + ' has been initiated.', true);
                                StackStore.populate(true);
                            },
                            error: function (request, status, error) {
                                alerts.showMessage('#error', 'Unable to perform ' + action.toLowerCase() + ' action on that stack. ' + JSON.parse(request.responseText).detail, true, 7000);
                            }
                        });
                    }
                });

            /*
             *  Using the DELETE verb is truly destructive. Terminates all hosts, terminates all
             *  EBS volumes, and deletes stack/host details from the stackd.io database.
             */
            } else {
                bootbox.confirm("<h4>Delete stack '"+stack.title+"'</h4><br />Please confirm that you want to delete this stack. Be advised that this is a completely destructive act that will stop, terminate, and delete all hosts, as well as the definition of this stack.", function (result) {
                    if (result) {
                        $.ajax({
                            url: stack.url,
                            type: 'DELETE',
                            headers: {
                                "X-CSRFToken": stackdio.settings.csrftoken,
                                "Accept": "application/json",
                                "Content-Type": "application/json"
                            },
                            success: function (response) {
                                alerts.showMessage('#success', 'Stack is currently being torn down and will be deleted once all hosts are terminated.', true, 5000);
                                StackStore.populate(true);
                            },
                            error: function (request, status, error) {
                                alerts.showMessage('#error', request.responseJSON.detail, true, 2000);
                            }
                        });
                    }
                });
            }
        }
    };
});