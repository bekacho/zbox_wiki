var auto_increase_width_size = function() {
    $(".auto-increase-width-size").focusin(function(evt) {
        $(this).css("width", "400px");
    });

    $(".auto-increase-width-size").focusout(function(evt) {
        $(this).css("width", "146px");
    });
}


$(document).ready(function() {
    auto_increase_width_size();
});