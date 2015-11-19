// A $( document ).ready() block.
$( document ).ready(function() {
    console.log( "Page is loaded!" );
    $(".js-loading").hide();

    $('#featured-videos-carousel').on('slide.bs.carousel', function () {
        if($(".featured-li").hasClass('active'))   {
             console.log( "Carousel event!" );
            $('.embedded-video').each(function( index ) {
                var url =$(this).attr('src');
                $('#this').attr('src', '');
                console.log( url );
                $(this).attr('src', url);
                //$(this).attr('src', $('iframe').attr('src'));
            });
        }
    })

    $(".js-submit").click(function() {
        $(this).hide();
        $(".js-loading").show();
        $(".js-loading-sound")[0].play();
    });


});