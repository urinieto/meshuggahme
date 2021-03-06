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

    $(window).keypress(function(evt) {
        if(evt.keyCode == 13)
            submit();
    });
    $(".js-submit").click(submit);

    function submit() {
        $(".js-submit").hide();
        $(".js-loading").show();
        $(".js-loading-sound")[0].play();
        //var clock = $('.load-clock').FlipClock( {
        //    interval: 10
        //});

        $.ajax({url: "/muxer/mux_demux?yt_url=" + $(".js-url-input").val(), dataType: "json", type: 'GET'})
            .done(function(results) {
                var status_url = results.status_url;
                var video_url = results.video_url;

                function pollVideo() {
                    $.ajax({
                        url: status_url,
                        type: 'GET',
                        dataType: "json", 
                        success : function(results) {
                            if(results.status == "complete") {
                                $(".js-video").attr("src", video_url);
                                $(".js-video")[0].load();

                                $(".js-loading").hide();
                                $(".js-submit").show();
                            } else {
                                setTimeout(pollVideo, 1000);
                            }
                        }
                    });
                }

                pollVideo();
            })
            .fail(function(evt) {
                $(".js-loading").hide();
                $(".js-submit").show();

                alert( "error" );
            });
    }


});