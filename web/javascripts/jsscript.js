// A $( document ).ready() block.
$( document ).ready(function() {
    console.log( "Page is loaded!" );

    $('#featured-videos-carousel').on('slide.bs.carousel', function () {
        console.log( "Carousel is moved!" );
    })
});