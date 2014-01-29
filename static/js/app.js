$(function() {
    // initialize blueImp gallery
    $("#links").click(function() {
        event = event || window.event;
        var target = event.target || event.srcElement,
                link = target.src ? target.parentNode : target,
                options = {index: link, event: event},
                links = this.getElementsByTagName('a');
        blueimp.Gallery(links, options);

    });

    // show/hide Delete link on messages
    $("#messages").children().hover(
        function() {
            $(this).children().eq(1).children().eq(2).removeClass("invisible");
        },
        function() {
            $(this).children().eq(1).children().eq(2).addClass("invisible");
        }
    );

    // submit login via Ajax
    $("#login-form").submit(function(event) {
        event.preventDefault();
        $.ajax({
            type: "POST",
            url: "/login",
            data: $(this).serialize(),
            success: function() {
                window.location = '/';
            },
            error: function() {
                $("#login-error").removeClass("hidden")
            }
        });
    });

    // member login form: workaround for 'disabled' input (First Name) not being submitted
    $("#update-profile-button").click(function(event) {
        $("#first_name").removeAttr("disabled")
        $("#update-profile-form").submit();
    })
});
