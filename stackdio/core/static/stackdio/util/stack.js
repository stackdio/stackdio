define(function() {
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
    };
});