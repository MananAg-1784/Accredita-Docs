var flash_msg = document.getElementById('flash_messages');
const socket = io("/profile",{autoConnect: false});
socket.connect();

socket.on('disconnect', function(){
    console.log("Socket disconnected...")
})

function check_status_code(code_data){
    var status = 'status' in code_data ? code_data['status'] : null;
    if(status == 400){
        console.log(code_data['error']);
        flash_msg.innerHTML = '';
        alert(code_data['error']);
        socket.disconnect();
        return 0
    } else {
        return 1
    }
}

function priv_button_enable(button_id, selected_priv, prev_priv){
    button_id = document.getElementById(button_id);
    if(selected_priv != prev_priv){
        button_id.classList.add('enable');
        button_id.disabled = false;
    }
    else{
        button_id.classList.remove('enable');
        button_id.disabled = true;
    }
}

function request_department(){
    if( !socket.connected){
        socket.connect()
    }
    var dept = document.getElementById('select-dept').value;
    console.log(dept)
    data_dict = {'department' : dept };
    socket.emit("dept_access", data_dict, (response) =>{
        response = JSON.parse(response);
        if(check_status_code(response)){
            if(response.error){
                flash_msg.innerHTML = "Server Error, Reload and try Again";
            } else {
                var a = document.getElementById('department');
                a.removeChild(a.lastElementChild);
                
                var d = document.createElement('div');
                d.innerHTML = `
                <div class="flex column gap-5">
                    <div class="flex row gap-5">
                        <strong>
                            Department : 
                        </strong>
                        <div>
                            <em>${dept}</em>
                        </div>
                    </div>
                    <strong>Access Requested</strong>
                </div>`
                a.appendChild(d);
            }
        }
    });
}

function select_tag(options, name, default_option, onchange_func = null ){
    var select_ = document.createElement('select');
    select_.setAttribute('name', name);
    select_.setAttribute('class', name);
    if(onchange_func){
        select_.setAttribute('onchange', onchange_func);
    }
   
    var option_selected = 0;
    for(var option_ of options){
        let option = new Option(option_, option_);
        if(option_ === default_option){
            option.selected = true;
            option_selected = 1
        }
        select_.add(option, undefined);
    }
    if(option_selected != 1){
        let option = new Option(default_option, '-1');
        option.disabled = true;
        option.selected = true;
        select_.add(option, undefined);
    }
    return select_
}