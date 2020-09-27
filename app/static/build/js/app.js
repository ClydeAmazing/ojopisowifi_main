$(function(){
    var token = $("input[name=csrfmiddlewaretoken]").val();
    var ip_add = $("input[name=input_ip]").val();
    var mac_add = $("input[name=input_mac]").val();

    var btn_done = document.getElementById("btn-done");

    if (btn_done.addEventListener){
        btn_done.addEventListener("click", Browse);
    }  else if (btn_done.attachEvent){
        btn_done.attachEvent("onclick", Browse);
    }   else {
        btn_done.onclick = Browse;
    }

    function Browse(){
        var data = {
            'csrfmiddlewaretoken': token,
            'ip': ip_add,
            'mac': mac_add
        }

        $.ajax({
            method: 'GET',
            url: '/app/browse',
            data: data,
            complete: function(){
                $('.card_main').fadeOut();
            },
            success: function(response){
                if (response['code'] == 200){
                    console.log(response['extra'])
                    clearInterval(q);
                    show_notification('success', 'fa fas-coins','<strong>P' + total_coins + '</strong> is credited successfully. Enjoy Surfing!')
                    setTimeout(function(){
                        if (redir_url){
                            window.location.href = redir_url
                        }else{
                            window.location.href = '/app/portal'
                        } 
                    }, 2000)

                }else{
                    show_notification('error', 'fas fa-exclamation-triangle',response['description'])
                }

            }
        })
    };

    var btn_insert_coin = document.getElementById("btn-insert-coin");

    if (btn_insert_coin.addEventListener){
        btn_insert_coin.addEventListener("click", InsertCoin);
    }else if (btn_insert_coin.attachEvent){
        btn_insert_coin.attachEvent("onclick", InsertCoin);
    }else {
        btn_insert_coin.onclick = InsertCoin;
    }

    function InsertCoin(){
        var data = {
            'csrfmiddlewaretoken': token,
            'ip': ip_add,
            'mac': mac_add
        }
        $('.btn-insert-coin').css('opacity', '0.5').attr('disabled', 'disabled');
        $.ajax({
            method: 'POST',
            url: '/app/slot',
            data: data,
            success: coinslot_status_success,
            error: coinslot_status_error
        })
    };

    var btn_gen_voucher = document.getElementById("gen_voucher");

    if (btn_gen_voucher !== null){
        if (btn_gen_voucher.addEventListener){
            btn_gen_voucher.addEventListener("click", GenerateVoucherCode);
        } else if (btn_gen_voucher.attachEvent){
            btn_gen_voucher.attachEvent("click", GenerateVoucherCode);
        } else {
            btn_gen_voucher.onclick = GenerateVoucherCode;
        }   
    }

    function GenerateVoucherCode(){
        $.ajax({
            method: 'GET',
            url: '/app/voucher',
            data: {
                'mac': mac_add
            },
            success: function(response){
                if (response['status'] == 'OK'){
                    $('input[name=input_voucher]').val(response['voucher_code'])
                    btn_gen_voucher.innerText = 'Done';
                    // CopyCode();
                    var btn_voucher_close = document.getElementById("btn_voucher_close");
                    btn_voucher_close.removeAttribute("data-dismiss");
                } else {
                    // $("#voucher-modal").modal('toggle');
                    window.location.href='/app/portal'
                    // window.location.href = "{% url 'app:portal' %}"
                }
            }

        })
    }

    var btn_copy = document.getElementById('btn_copy');

    if (btn_copy != null){
        if (btn_copy.addEventListener){
            btn_copy.addEventListener("click", CopyCode);
        } else if (btn_copy.attachEvent){
            btn_copy.attachEvent("click", CopyCode);
        } else {
            btn_copy.onclick = CopyCode;
        }   
    }

    function CopyCode(){
        var input_voucher = document.getElementById('input_voucher');
        input_voucher.select();
        input_voucher.setSelectionRange(0,99999);
        document.execCommand('copy');
        input_voucher.setSelectionRange(0,0);
        show_notification('success', 'fa fa-copy','<strong>Voucher code copied to clipboard</strong>')
    }

    var btn_voucher_close = document.getElementById("btn_voucher_close");

    if (btn_voucher_close != null){
        if (btn_voucher_close.addEventListener){
            btn_voucher_close.addEventListener("click", CloseVoucher);
        } else if (btn_voucher_close.attachEvent){
            btn_voucher_close.attachEvent("click", CloseVoucher);
        } else {
            btn_voucher_close.onclick = CloseVoucher;
        }
    }

    function CloseVoucher(){
        if (btn_voucher_close.getAttribute('data-dismiss') !== 'modal'){
            clearInterval(q);
            window.location.href='/app/portal';
        }
    }

    $('.btn_redeem_voucher').on('click', function(){
        voucher = $(this).attr('data-voucher');
        Redeem(voucher);
        $("#voucher-list-modal").modal('toggle');
    })

    $('#btn_voucher_redeem').on('click', function(){
        voucher = $('input[name=input_voucher_redeem]').val();
        if(voucher){
            Redeem(voucher);
        }
    })

    function Redeem(voucher){
        $.ajax({
            method: 'POST',
            url: '/app/redeem',
            data: {
                'csrfmiddlewaretoken': token,
                'voucher': voucher,
                'ip': ip_add,
                'mac': mac_add
            },
            beforeSend: function(){
                $('#loadMe').modal('toggle');
            },
            complete: function(){
                $('#loadMe').modal('toggle');
            },
            success: function(response){
                if(response['code'] == 200){
                    show_notification('success', 'fas fa-barcode','<strong>Voucher code ' + response['voucher_code'] + ' successfully redeemed!</strong>')
                    
                }else{
                    show_notification('error', 'fas fa-exclamation-triangle','<strong>' + response['description'] + '</strong>')
                }

                setTimeout(function(){
                    window.location.href='/app/portal'
                }, 2000)
            }
        })

    }

    var btn_pause_resume = document.getElementById("btn-pause-resume");

    if (btn_pause_resume !== null){
        if (btn_pause_resume.addEventListener){
            btn_pause_resume.addEventListener("click", PauseResume);
        } else if (btn_pause_resume.attachEvent){
            btn_pause_resume.attachEvent("onclick", PauseResume);
        } else {
            btn_pause_resume.onclick = PauseResume;
        }
    }
    
    function PauseResume(){
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
            error: coinslot_status_error,
            beforeSend: function(){
                $('#conn_stat').text('Processing..')
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

                        show_notification('error', 'fas fa-exclamation-triangle','<strong>Internet connection paused.</strong> Resume when you\'re ready.')
                        clearInterval(timer);

                    }else if (x == 'Connected'){
                        html = "<span class='fas fa-pause'></span> Pause"
                        $('.btn-pause-resume').removeClass('btn-info').addClass('btn-danger')
                        $('.btn-pause-resume').attr('data-action', 'pause')
                        $('.btn-pause-resume').html(html)
                        $('#conn_stat').removeClass('text-warning').addClass('text-success').text('Connected')
                        
                        show_notification('success', 'fas fa-wifi','<strong>Internet connection resumed.</strong> Enjoy browsing the internet.')
                        start_timer();
                    }
               }else{
                    show_notification('error', 'fas fa-exclamation-triangle', response['description'])
               }
            }
        })
    };

    var retry_count = 2;
    var q;

    function coinslot_status_success(response)  {
        response_code = response['code']
        response_desc = response['description']

        if (response_code == 600){
            show_notification('error', 'fas fa-exclamation-triangle', '<strong>' + response_desc + '</strong>')
            setTimeout(function(){
                $('.btn-insert-coin').css('opacity', '1').removeAttr('disabled');
            }, retry_count * 1000)

            retry_count += 1

        }else if(response_code == 200){
            show_notification('info', 'fas fa-coins','<strong>Insert coin(s).</strong>');
            $('.slot_countdown').css('width', '100%');
            var connection_status = $('#conn_stat').html()
            var token = $('input[name=csrfmiddlewaretoken]').val();
            var ip_add = $('input[name=input_ip]').val();
            var mac_add = $('input[name=input_mac]').val();
            var data = {
                'csrfmiddlewaretoken': token,
                'ip': ip_add,
                'mac': mac_add
                }

            countdown();

            q = setInterval(function(){
                $.ajax({
                    method: 'GET',
                    url: '/app/commit',
                    data: data,
                    success: fetch_queue_info
                })

                function fetch_queue_info(response){
                    if (response['Status'] == 'Available'){
                        clearInterval(q);
                        $('#conn_stat').html(connection_status).removeClass('blinking');
                        show_notification('error', 'fas fa-stopwatch', '<strong>Slot timeout.</strong>');
                        setTimeout(function(){
                                    $('.btn-insert-coin').css('opacity', '1').removeAttr('disabled');
                                    $('.btn-pause-resume').removeAttr('disabled');
                            }, 2000)
                    }

                    if (response['Total_Coins'] > total_coins){
                        countdown();
                        total_coins = response['Total_Coins'];

                        total_time = new Date(null);
                        total_time.setSeconds(response['Total_Time']);
                        total_time_val = total_time.getTime();

                        $('.btn-done').removeClass('btn-outline-default').addClass('btn-outline-success');
                        $('.btn-done').html('<span class="fas fa-paper-plane">\
                                            </span><b> Surf the Net!</b><span class="badge badge-pill badge-warning ml-1 p-1">\
                                            <strong>P ' + total_coins + '</strong></span>');
                        $('.btn-done').removeAttr('disabled');
                        $('.lbl_coins_inserted').text('P ' + total_coins);
                        msg = 'Total of <strong>P' + total_coins + '</strong> is loaded. <strong>(+' + time_formatter(total_time_val) + ')</strong>';
                        show_notification('info', 'fa fas-coins', msg);

                        var vcode = document.getElementById('vcode')

                        if (voucher_flg==1){
                            if(vcode==null){
                                $('#divInsertCoin').append('<div class="row" id="vcode"> <div class="col text-center">  \
                                                <button type="button" class="animated fadeIn btn btn-md btn-rounded btn-warning" data-toggle="modal" data-target="#voucher-modal"> \
                                                <span class="fas fa-barcode"></span> Get Voucher Code </button> </div> </div>')
                            }
                        }
                    }
                }

            }, 1000 )

            retry_count = 2;

        }else{
            show_notification('error','fas fa-exclamation-triangle', response_desc)
            setTimeout(function(){
                        $('.btn-insert-coin').css('opacity', '1').removeAttr('disabled');
                        $('.btn-pause-resume').removeAttr('disabled');

                        $('.slot_countdown').stop();
                        $('.slot_countdown').css('width', '0%');
                }, 2000)
        }
    }

    function countdown(){
        $('#conn_stat').html('Insert coins..').addClass('blinking')
        $('.slot_countdown').stop();
        $('.slot_countdown').css('width', '100%');
        $('.slot_countdown').animate({'width': '0%'}, (slot_timeout-2) * 1000);
        $('.btn-pause-resume').attr('disabled', 'disabled');
    }

    // Error function if for some reason, unable to connect to the main server
    function coinslot_status_error(jqXHR, textStatus, errorThrown){
        show_notification('error', 'fas fa-exclamation-triangle','<strong>Unable to connect. Please check connection or <a href="/app/portal">resfresh</a> this page.</strong>')
        console.log(jqXHR)
        console.log(textStatus)
        console.log(errorThrown)
    }

    // PNotify setup
    PNotify.prototype.options.styling = "bootstrap3";
    var stack_bottomright = {"dir1":"up", "dir2":"up", "push":"top"};

    function show_notification(type, icon, message){
        PNotify.removeAll();
        var options = {
            text: message,
            type: type,
            addclass: "stack-bottomright",
            stack: stack_bottomright,
            icon: icon,
            animate: {
                animate: true,
                in_class: 'rotateInDownLeft',
                out_class: 'rotateOutUpRight'
            }
        };

        new PNotify(options);
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

    var timer;
    function start_timer(){
        var init_time = new Date();

         timer = setInterval(function(){
            var elapsed = new Date() - init_time;
            var distance = day_time_left - elapsed;

            var time = time_formatter(distance)
            $('.time_holder').html(time)
            if (distance < 0){
                clearInterval(timer);
                timeout = '<span class = "text-danger"><strong>TIMEOUT</strong></span>'
                $('#conn_stat').html('Disconnected').addClass('text-danger')
                $('.con_status_holder').html(timeout)
                $('.btn-extend').text('Insert Coin')
                $('.btn-pause-resume').attr('disabled', 'disabled')

                show_notification('error', 'fas fa-exclamation-triangle', '<strong>Connection timeout.</strong> Insert coin(s) to continue browsing.')
                setTimeout(function(){
                    window.location.href='/app/portal'
                }, 3000)
            }
        }, 1000)
    };

    //Time formatter
    function time_formatter(mins){
        var days = Math.floor(mins / (1000 * 60 * 60 * 24));
        var hours = Math.floor((mins % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        var minutes = Math.floor((mins % (1000 * 60 * 60)) / (1000 * 60));
        var seconds = Math.floor((mins % (1000 * 60)) / 1000);

        str_time = ''
        if (days > 0){
            str_time += days + "d "
        }
        if (hours > 0){
            str_time += hours + "h "
        }
        if (minutes > 0){
            str_time += minutes + "m "
        }
        if (seconds > 0){
            str_time += seconds + "s "
        }
        return str_time
    }

    $( window ).on('beforeunload', function( event ) {
        $("#loadMe").modal({
          backdrop: "static",
          keyboard: false,
          show: true
        });
    });
})