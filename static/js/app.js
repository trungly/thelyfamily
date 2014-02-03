$(function() {

    // submit login via Ajax
    $("#login-form").submit(function(event) {
        event.preventDefault();
        $.ajax({
            type: "POST",
            url: "/login",
            data: $(this).serialize(),
            success: function() {
                window.location.reload();
            },
            error: function() {
                $("#login-error").removeClass("hidden")
            }
        });
    });

});
