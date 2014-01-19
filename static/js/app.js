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
});
