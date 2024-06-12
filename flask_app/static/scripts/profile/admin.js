sec = document.getElementById('other-admin-data');

socket.on('connect', function(){
    console.log("Socket Connected...");
    sec.innerHTML = '';

    // get the list of all the dept users and append to the users body
    get_dept_users();
});

function get_dept_users(){
    flash_msg.innerHTML = '<div class="loader" style="top: 2px; position: relative;"></div><div>Loading Department Teacher Data...</div>';
    data_dict = {'email': user.email };
    socket.emit('dept_users', data_dict, (response)=> {
        response = JSON.parse(response);
        console.log(response);
        if(check_status_code(response)){
            if(response.error){
                flash_msg.innerHTML = "Access denied or Reload";
            } else {
                response = response.response;
                dept_users = response['dept_users'];
                privs = response['available-privs'];

                sec.innerHTML = dept_users;
            }
        }
        flash_msg.innerHTML = '';
    }); 
}

function change_priv(email, priv, id_){
    if( !socket.connected){
        socket.connect();
    }   
    parent_email = email;
    if (priv == 1){
        priv = document.querySelector(`#privilage_${id_}`).value;
    } 
    parent_priv = priv;
    console.log(parent_email, parent_priv);
    flash_msg.innerHTML = "<div class='loader'></div><div>Granting Access</div>"
    if(parent_priv == 'denied'){
        flash_msg.innerHTML = "<div class='loader'></div><div>Dening Access</div>"
    }
    data_dict =  {'privilage' : parent_priv, "email" : parent_email};
    socket.emit("priv_grant", data_dict , (response) =>{
        response = JSON.parse(response);
        if(check_status_code(response)){
            if(response.error){
                flash_msg.innerHTML = "Cannot Change privilage, Try Again";
            } else {
                get_dept_users();
                flash_msg.innerHTML = 'Privilage Changed...';
            }
        }
    });
}

function remove_user(email){
    console.log(email);
    if( !socket.connected){
        socket.connect();
    }   
    console.log(email);
    flash_msg.innerHTML = "<div class='loader'></div><div>Removing User</div>"
    socket.emit("remove_user", email , (response) =>{
        response = JSON.parse(response);
        if(check_status_code(response)){
            if(response.error){
                flash_msg.innerHTML = "Cannot Remove User, Try Again";
            } else {
                get_dept_users();
                flash_msg.innerHTML = 'User Successfully Removed...';
            }
        }
    });
}
