if (Meteor.isClient) {

    Template.sidebarTemplate.events({
        'click .navlink': function (evt, node) {
            $('.navlink').removeClass('active');
            $('.view').hide();
            $('#'+evt.target.parentNode.id).addClass('active');
        },
        'click #stacks-href': function (evt,node) {
            // console.log(evt.target.parentNode.id.toString().split('-')[0]);
            $('#stacks').show();
        },
        'click #dashboard-href': function () {
            $('#dashboard').show();
        },
        'click #providers-href': function () {
            $('#providers').show();
        },
    });

}

if (Meteor.isServer) {
  Meteor.startup(function () {
    // code to run on server at startup
  });
}


