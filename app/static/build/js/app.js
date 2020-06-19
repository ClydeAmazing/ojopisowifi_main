$(function(){
    //TODO: Capture original requested page
    //Global variables
    var token = $('input[name=csrfmiddlewaretoken]').val();
    var ip_add = $('input[name=input_ip]').val();
    var mac_add = $('input[name=input_mac').val();
    //var total_coins;

    $('.btn-done').on('click', function(){
        var data = {
            'csrfmiddlewaretoken': token,
            'ip': ip_add,
            'mac': mac_add
        }

        $.ajax({
            method: 'GET',
            url: '/app/browse',
            data: data,
            beforeSend: function(){
                $(this).html('Loading...')
            },
            complete: function(){
                $('.card_main').fadeOut();
                s('.loading').show();
            },
            success: function(response){
                if (response['code'] == 200){
                    //show_notification('success', total_coins + ' is credited successfully. Enjoy Surfing!')
                    setTimeout(function(){
                        window.location.href = '/app/portal'
                    }, 3000)

                }else{
                    show_notification('error', response['description'])
                }

            }
        })
    });

    $('.btn-insert-coin').on('click', function(){
        var data = {
            'csrfmiddlewaretoken': token,
            'request': 'reserve',
            'ip': ip_add,
            'mac': mac_add
        }

        $.ajax({
            method: 'POST',
            url: '/app/slot',
            data: data,
            success: coinslot_status_success,
            error: coinslot_status_error
        })
    });

    $('.btn-pause-resume').on('click', function(){
        var action = $('.btn-pause-resume').attr('data-action')

        var data = {
            'csrfmiddlewaretoken': token,
            'ip': ip_add,
            'mac': mac_add,
            'action': action
        }

        $.ajax({
            method: 'GET',
            url: '/app/pause',
            data: data,
            beforeSend: function(){
                $('#conn_stat')..text('Processing..')
                $('.btn-pause-resume').css('opacity', '0.5').attr('disabled', 'disabled')
            },
            complete: function(){
                $('.btn-pause-resume').css('opacity', '1').removeAttr('disabled');
            },
            success: function(response){
               if (response['code'] = 200){
                    x = response['description']
                    if (x == 'Paused'){
                        html = "<span class='fas fa-play'></span> Resume"
                        $('.btn-pause-resume').removeClass('btn-danger').addClass('btn-info')
                        $('.btn-pause-resume').attr('data-action', 'resume')
                        $('.btn-pause-resume').html(html)
                        $('#conn_stat').removeClass('text-success').addClass('text-warning').text('Paused')

                        show_notification('error', '<strong>Internet connection paused.</strong> Resume when you\'re ready.')
                        clearInterval(timer);

                    }else if (x == 'Connected'){
                        html = "<span class='fas fa-pause'></span> Pause"
                        $('.btn-pause-resume').removeClass('btn-info').addClass('btn-danger')
                        $('.btn-pause-resume').attr('data-action', 'pause')
                        $('.btn-pause-resume').html(html)
                        $('#conn_stat').removeClass('text-warning').addClass('text-success').text('Connected')
                        show_notification('success', '<strong>Internet connection resumed.</strong> Enjoy browsing the internet.')

                        start_timer();
                    }
               }else{
                    show_notification('error', response['description'])
               }
            },
            error: coinslot_status_error
        })
    });

    var retry_count = 2;

    function coinslot_status_success(response)  {
        response_code = response['code']
        response_desc = response['description']

        if (response_code == 600){
            show_notification('error', '<strong>' + response_desc + '</strong>')
            $('.btn-insert-coin').css('opacity', '0.5').attr('disabled', 'disabled');
            setTimeout(function(){
                $('.btn-insert-coin').css('opacity', '1').removeAttr('disabled');
            }, retry_count * 1000)

            retry_count += 1

        }else if(response_code == 200){
            show_notification('info', '<strong>Insert coin(s).</strong>');
            $('.slot_countdown').css('width', '100%');
            $('.btn-insert-coin').css('opacity', '0.5').attr('disabled', 'disabled');
            var token = $('input[name=csrfmiddlewaretoken]').val();
            var ip_add = $('input[name=input_ip]').val();
            var mac_add = $('input[name=input_mac').val();
            var data = {
                'csrfmiddlewaretoken': token,
                'request': 'release',
                'ip': ip_add,
                'mac': mac_add
                }

            var time_countdown = slot_timeout

            function countdown(){
                $('.slot_countdown').stop();
                $('.slot_countdown').css('width', '100%');
                $('.slot_countdown').animate({'width': '0%'}, slot_timeout * 1000);
            }
            countdown();

            var q = setInterval(function(){
                $.ajax({
                    method: 'GET',
                    url: '/app/commit',
                    data: data,
                    success: fetch_queue_info
                })

                function fetch_queue_info(response){
                    if (response['Total_Coins'] != total_coins){
                        countdown();
                        time_countdown = slot_timeout;
                        total_coins = response['Total_Coins']
                        $('.btn-done').html('(' + total_coins + ') Surf the Net!');
                        $('.btn-done').removeAttr('disabled');

                        if (response['Total_Coins'] > 0){
                            msg = 'Total of <strong>₱' + total_coins + '</strong> is loaded.'
                            show_notification('info', msg)
                        }

                    }else{
                        time_countdown = time_countdown - 1;
                    }
                }

                if (time_countdown == 1){
                    clearInterval(q)
                    $.ajax({
                        method: 'POST',
                        url: '/app/slot',
                        data: data,
                        success: function(){

                            show_notification('error', '<strong>Slot timeout.</strong>')
                            setTimeout(function(){
                                        $('.btn-insert-coin').css('opacity', '1').removeAttr('disabled');
                            }, 2000)
                        },
                        error: coinslot_status_error
                    })
                }
            }, 1000 )

            retry_count = 2;

        }else{
            show_notification('error', response_desc)
        }
    }

    // Error function if for some reason, unable to connect to the main server
    function coinslot_status_error(jqXHR, textStatus, errorThrown){
        show_notification('error', '<strong>Unable to connect to wifi. Please check connection.</strong>')
    }

    // PNotify setup
    PNotify.prototype.options.styling = "bootstrap3";
    var stack_bottomright = {"dir1":"up", "dir2":"up", "push":"top"};

    function show_notification(type, message){
        var options = {
            text: message,
            type: type,
            addclass: "stack-bottomright",
            stack: stack_bottomright,
            animate: {
                animate: true,
                in_class: 'rotateInDownLeft',
                out_class: 'rotateOutUpRight'
            }
        };

        new PNotify(options)
    }

    //Timer Setup
    var time_left = new Date(null);
    time_left.setSeconds(seconds_left);
    var day_time_left = time_left.getTime();

    //Set initial time left
    time = time_formatter(day_time_left)
    $('.time_holder').html(time)

    //Countdown if not paused
    if (conn_status != 'Paused' && seconds_left > 0){
        start_timer();
    }

    var initial_time = new Date().getTime();
    var timer;
    var counter = 1;
    function start_timer(){
         timer = setInterval(function(){
            //current_time = new Date().getTime();
            //tock = current_time - initial_time
            //distance = day_time_left - (Math.floor(tock/1000)*1000)
            distance = day_time_left - (counter * 1000)
            time = time_formatter(distance)
            $('.time_holder').html(time)
            if (distance == 0){
                clearInterval(timer);
                timeout = '<span class = "text-danger"><strong>TIMEOUT</strong></span>'
                $('#conn_stat').html('Disconnected').addClass('text-danger')
                $('.con_status_holder').html(timeout)
                $('.btn-extend').text('Insert Coin')
                $('.btn-pause-resume').attr('disabled', 'disabled')

                show_notification('error', '<strong>Connection timeout.</strong> Insert coin(s) to continue browsing.')
                setTimeout(function(){
                    window.location.href='/app/portal'
                }, 3000)
            }
            counter ++;
        }, 1000)
    };

    //Time formatter
    function time_formatter(mins){
        var days = Math.floor(mins / (1000 * 60 * 60 * 24));
        var hours = Math.floor((mins % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var minutes = Math.floor((mins % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((mins % (1000 * 60)) / 1000);

        time = ''
        if (days > 0){
            time += days + "d "
        }
        if (hours > 0){
            time += hours + "h "
        }
        if (minutes > 0){
            time += minutes + "m "
        }

        time += seconds + "s "

        return time
    }
})