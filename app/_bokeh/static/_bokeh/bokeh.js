function sidebar_collapse() {
    // var h = document.documentElement.clientHeight;
    var w = document.documentElement.clientWidth;
    var btn_aria = $('button#sidebar-toggle').attr('aria-expanded');

    if (w >= 767 && btn_aria == 'false' ||
        w <  768 && btn_aria == 'true') {
        $('button#sidebar-toggle').click();
    }
}

window.onresize = function(event) {
    sidebar_collapse();
}


$(document).ready(function() {
    $('#topnav').on('shown.bs.collapse', function(event) {
                $("#sidebar").collapse('hide');
        });
    $('#sidebar').on('shown.bs.collapse', function(event) {
                $("#topnav").collapse('hide');
        });
});

