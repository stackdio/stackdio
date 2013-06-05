if (Meteor.isClient) {
    Template.sidebarTemplate.rendered = function () {

        $(function(){
            $("[data-hide]").on("click", function () {
                // $("." + $(this).attr("data-hide")).hide();
                // -or-, see below
                $(this).closest("." + $(this).attr("data-hide")).hide();
            });
        });

        $('#settings').on('click', function () {
            $('#aws-account-fail').show();
            
        });
    }
}

if (Meteor.isServer) {
  Meteor.startup(function () {
    // code to run on server at startup
  });
}


