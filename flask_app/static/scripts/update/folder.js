function add_folder(){
    console.log("Adding folder");

    var add_folder = document.getElementById('add_folder');

    var folder_ = document.createElement('div');
    folder_.classList.add('flex', 'row', 'gap-10', 'align-center');
    folder_.setAttribute('id', 'folder_options');
    
    var label_ = document.createElement('span')
    label_.innerHTML = 'Folder :';
    var options = [];
    var values = [];
    for(var _ of drive_folders){
        options.push(_.name);
        values.push(_.name);
    }
    var select_ = select_tag(
        options = options,
        name='select_folder',
        default_option = 'Select Folder',
        onchange_func = "selected_folders(this.parentNode)",
        value = values );
    folder_.appendChild(label_);
    folder_.appendChild(select_);
    
    var label_ = document.createElement('span')
    label_.innerHTML = 'Accredition :';
    var select_ = select_tag(
        options = accredition,
        name='select_accredition',
        default_option = accredition[0],
        onchange_func = "selected_folders(this.parentNode)");
    folder_.appendChild(label_);
    folder_.appendChild(select_);
    
    var cancel_ = document.createElement('div');
    cancel_.classList.add('flex');
    cancel_.setAttribute('onclick', "remove_folder(this.parentNode)");
    cancel_.innerHTML = `
        <img src='/static?file_name=x-circle-regular-24.png'></img>
    `;
    folder_.appendChild(cancel_);
    add_folder.appendChild(folder_);
}

function create_folder(){
    var cat_options = document.getElementById('category_options');
    cat_options.style.display="flex";

    cat_options.innerHTML = `
    <div class="flex column gap-10">
        <div id="more_options_"></div>
        <div class="flex row gap-25" style="justify-content: space-between;">
            <div style="font-size: 19px; font-weight: 600;">
            Create New Folder (My Drive)
            </div>
            <div class="flex align-center" onclick="remove_options_for_category()" style="cursor: pointer;">
                <img src="/static?file_name=x-regular-24.png" alt="" style="height: 25px;">
            </div>
        </div>
        <div class="flex column gap-10">
            <div class="flex column gap-5">
                <label for="new_folder_name">Name of the Folder</label>
                <input type="text" name="new_folder_name" id="new_folder_name" placeholder="Enter the Folder Name">
            </div>
            <div id="select_accredition_new" class="flex column gap-5">
                <label for="new_accredition">Select Accredition</label>
            </div>
            <label for="new_folder_name">
                    <em>Note : A new folder will be created in your drive and shared</em>
                    <br>
                    <em> with rest of the department</em>
            </label>
            <button onclick="create_folder_submit()" id="add_new_cat">Create</button>
        </div>
    </div>
    `;
    var select_ = select_tag(
        options = accredition,
        name='new_folder_accredition',
        default_option = accredition[0],
        onchange_func = "selected_folders(this.parentNode)");
    document.getElementById('select_accredition_new').appendChild(select_);
}

function create_folder_submit(){
    folder_name = document.getElementById('new_folder_name').value;
    accredition_value = document.querySelector('.new_folder_accredition').value;
    console.log(folder_name, accredition);

    if(folder_name != '' && accredition != ''){
        display_prog("<div class='loader'></div><div>Creating...</div>", false);
        socket_connect();
        json = {'folder_name':folder_name,'accredition' : accredition_value};
        socket.emit('create-folder', json, (response)=>{
            response = JSON.parse(response);
            console.log(response);
            flash_msg.innerHTML = '';
            if(check_status_code(response)){
                if(response.error){
                    display_prog(response.error);
                } else {
                    document.getElementById('category_options').style.display = 'none';
                    display_prog("New Folder is Created");
                    load_folder_data();

                    var folder_ = document.createElement('div');
                    folder_.classList.add("flex","gap-10","align-center");
                    folder_.style.justifyContent = "space-between";
                    folder_.innerHTML = `
                        <span class="folder-name  cut-text">${json.folder_name}</span>
                        <div style="height: 100%; overflow: hidden; display:flex; align-items:stretch;">
                            <span style="border:1px solid white;"></span>
                        </div>
                        <span class="folder-accredition">${json.accredition}</span>
                    `;
                    document.getElementById('selected-folder-list').appendChild(folder_);
                }
            }
        });
    } 
}

function remove_folder(childNode){
    document.getElementById('add_folder').removeChild(childNode)
    selected_folders(false);
}

function selected_folders(parent_node){
    var folders_added = document.querySelectorAll('#add_folder >div');
    folder_list = document.getElementById('selected-folder-list');
    folder_list.innerHTML = '';
    folders = [];

    for( var a of folders_added){
        var selectedFolder = a.getElementsByClassName('select_folder')[0].value;
        var selectedAccredition = a.getElementsByClassName('select_accredition')[0].value;
        console.log(selectedFolder, selectedAccredition);
        var data = `
            <span class="folder-name  cut-text">${selectedFolder}</span>
            <div style="height: 100%; overflow: hidden; display:flex; align-items:stretch;">
                <span style="border:1px solid white;"></span>
            </div>
            <span class="folder-accredition">${selectedAccredition}</span>
            `
        var flag = 0;
        for (var x of folder_list.childNodes){
            var sf = x.getElementsByClassName('folder-name')[0].innerHTML;
            var sa = x.getElementsByClassName('folder-accredition')[0].innerHTML;
            if( selectedFolder == sf && selectedAccredition == sa ){
                flag = 1;
                break;
            }
        }
        if(flag != 1 && selectedFolder!= '1'){
            var div_ = document.createElement('div');
            div_.classList.add('flex','row','gap-10','align-center');
            div_.style.justifyContent = "space-between";
            div_.innerHTML = data;
            folder_list.appendChild(div_);
            folders.push({
                folder_name:selectedFolder,
                accredition:selectedAccredition
            })
        }
    }    
}

function submit_folder_list(){
    var selected_folder = document.querySelectorAll('#selected-folder-list > div');
    console.log("List of Folders : ", selected_folder);
    var res = [];
    for(var folder of selected_folder){
        var sf = folder.getElementsByClassName('folder-name')[0].innerHTML;
        var sa = folder.getElementsByClassName('folder-accredition')[0].innerHTML;
        res.push( {'name': sf, 'accredition': sa} );
    }
    console.log("List of Folders to be modified : ",res);

    var json = {'folders' : res}
    display_prog('<div class="loader"></div><div>Updating</div>', false);
    socket_connect();
    socket.emit('modify-folder-list',json, (response)=>{
        response = JSON.parse(response);
        console.log(response);
        if(check_status_code(response)){
            if(response.error){
                display_prog(response.error);
            } else {
                display_prog("Folder List Updated");
            }
        }
    });


}
