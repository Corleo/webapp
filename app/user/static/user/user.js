$( document ).ready(function() {
    $("#div-password")
        .mousedown(function(){
            $("#div-password span").removeClass('glyphicon-eye-close').addClass('glyphicon-eye-open');
            $("#div-password input").attr('type','text');
        })
        .on('mouseup mouseleave', function(){
            $("#div-password span").removeClass('glyphicon-eye-open').addClass('glyphicon-eye-close');
            $("#div-password input").attr('type','password').focus();
        });

    $("#div-confirm")
        .mousedown(function(){
            $("#div-confirm span").removeClass('glyphicon-eye-close').addClass('glyphicon-eye-open');
            $("#div-confirm input").attr('type','text');
        })
        .on('mouseup mouseleave', function(){
            $("#div-confirm span").removeClass('glyphicon-eye-open').addClass('glyphicon-eye-close');
            $("#div-confirm input").attr('type','password').focus();
        });

}); // $( document )
