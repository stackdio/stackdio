if (Meteor.isClient) {

    $('#dashboard').show();

    Template.sidebarTemplate.events({
        'click .navlink': function (evt, node) {
            var id, ele = evt.target;

            while (ele.id === '') {
                if (!ele.hasOwnProperty('parentNode')) break;
                ele = ele.parentNode;
            }

            id = ele.id.toString();

            $('.navlink').removeClass('active');
            $('.view').hide();
            $('#' + id).addClass('active');
            $('#' + id.split('-')[0]).show();
        }
    });

}

if (Meteor.isServer) {
  Meteor.startup(function () {
    // code to run on server at startup
  });
}


