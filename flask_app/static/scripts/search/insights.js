
var get_insight = 1;

function get_insights(){
    flash_msg.innerHTML = '<div class="loader"></div><div>Loading Insights...</div>';
    document.getElementById('insights_data_').innerHTML = '';
    document.getElementById('select_folder_').disabled = true;
    folders_ = []
    for(var x of folders){
        folders_.push(x.folder);
    }
    if(folders_.length == 0){
        flash_msg.innerHTML = "Add Folders To the Department";
        return
    }
    console.log('Folder name : ', folders_);
    socket.emit('get_folder_insights',{'folder':folders_},(response)=>{
        response = JSON.parse(response);
        console.log("Recieved data...", response);
        if(check_status_code(response)){
            if(response.error){
                flash_msg.innerHTML = response.error;
            } else{
                flash_msg.innerHTML = '';
                document.getElementById('insights_data_').innerHTML = response.response;
                document.getElementById('select_folder_').disabled = false;
                get_folder_insights();
            }
        }
    });
}

function display_insights(){
    document.getElementById('insights_display_button').classList.add('hide');
    document.getElementById('insights_data').classList.remove('hide');
    document.getElementById('search_results').classList.add('hide');
    if(get_insight == 1){
        get_insights();
        get_insight += 1;
    }
    get_folder_insights();
}

function reset_insights(){
    document.getElementById('search_results').classList.remove('hide');
    document.getElementById('insights').classList.remove('hide');
    document.getElementById('insights_display_button').classList.remove('hide');
    document.getElementById('insights_data').classList.add('hide');
}

function get_folder_insights(){
    parent = document.getElementById('select_folder_');
    var options = parent.options;
    var folder = parent.value;

    for(var x of options){
        console.log(x.value);
        var data = document.getElementById(x.value+'_insight');
        console.log(data);
        if(x.value !== '-1'){
            if(x.value === folder){
                data.classList.remove('hide');
            } else{
                data.classList.add('hide');
            }
        }
    }
}


function ignore_file(name, folder, reason){
    json = {'drive_id': name, 'folder': folder, 'reason':reason};
    document.getElementById('display_options_response').innerHTML = `
    <div class="flex row gap-10" style="padding-right: 10px">
    <div class="loader"></div><div>Ignoring File</div>
    </div>
    `;
    document.getElementById('display_options_response').classList.remove('hide');
    socket.emit('ignore_file',(json), (response)=>{
        response = JSON.parse(response);
        console.log(response);
        if(check_status_code(response)){
            var display_ = "";
            if(response.error){
                display_ = response.error;
            } else {
                display_ = "File Ignored";
            }
            document.getElementById('display_options_response').innerHTML = `
            <div>${display_}</div>
            <div class="flex align-center" onclick="remove_activity_log()">
                <img src="/static?file_name=x-regular-white-24.png">
            </div>
            `;
           
            setTimeout(() => {
                document.getElementById('display_options_response').classList.add('hide');
            }, 5000);
        }
    });
}

function include_file(name, folder){
    json = {'drive_id': name, 'folder': folder};
    document.getElementById('display_options_response').innerHTML = `
    <div class="flex row gap-10" style="padding-right: 10px">
    <div class="loader"></div><div>Including File</div>
    </div>
    `;
    document.getElementById('display_options_response').classList.remove('hide');
    socket.emit('include_file',(json), (response)=>{
        response = JSON.parse(response);
        console.log(response);
        if(check_status_code(response)){
            var display_ = "";
            if(response.error){
                display_ = response.error;
            } else {
                display_ = "File Included";
            }
            document.getElementById('display_options_response').innerHTML = `
            <div>${display_}</div>
            <div class="flex align-center" onclick="remove_activity_log()">
                <img src="/static?file_name=x-regular-white-24.png">
            </div>
            `;
           
            setTimeout(() => {
                document.getElementById('display_options_response').classList.add('hide');
            }, 5000);
        }
    })
}

function insights_overlay_option(drive_id, name){
    var overlay = document.getElementById("overlay");
    overlay.style.display = "flex";
    overlay.innerHTML = `
    <div class="flex column gap-10">
        <div class="flex column gap-5">
            <div class="flex row gap-25" style="justify-content: space-between;">
                <div style="font-size: 19px; font-weight: 600;">
                Formatting Files
                </div>
                <div class="flex align-center" onclick="remove_options_for_overlay()" style="cursor: pointer;">
                    <img src="/static?file_name=x-regular-24.png" alt="" style="height: 25px;">
                </div>
            </div>
            <div>
                <em>File naming format : yyyymmdd_(code)_(file-name)</em>
            </div>
        </div>
        <div class="flex column gap-15">
            <div class="flex column gap-5" id="new_file_name_">
                <div>Change or Add File Name</div>
                <input type="text" id="new_file_name_insights" placeholder="Enter file name" name="new_file_name_">
            </div>
            <div class="flex column gap-5" id="add_category_disp_options">
                <div>Add Category to the file</div>
            </div>
            <div class="flex row gap-15">
                <button onclick="rename_file_insights('${drive_id}')">
                    Rename
                </button>
                <button onclick="add_file_category_insights('${drive_id}')">
                    Add Only Category
                </button>
            </div>
        </div>
    </div>
    `;
    
    var select_= document.createElement('select');
    select_.setAttribute('id','new_file_format_category');
    select_.setAttribute('onchange','');
    for (var x of category) {
        let option = new Option(`${x.definition} - ${x.category}`,x.category);
        select_.add(option, undefined);
    }
    
    document.getElementById('add_category_disp_options').appendChild(select_);
    
    $('#new_file_format_category').select2({
        width: '340px',
        placeholder:"Search and Select Category",  
        closeOnSelect: true,
    });
    $('#new_file_format_category').val('').trigger('change');
    console.log("File name : ", name);
    document.getElementById('new_file_name_insights').value = name; 
}

function rename_file_insights(id){
    file_name = document.getElementById('new_file_name_insights').value; 
    category = document.getElementById('new_file_format_category').value;
    console.log(file_name, category);
    
    json = {'drive_id': id, 'name': file_name, 'category' : category};
    document.getElementById('display_options_response').innerHTML = `
    <div class="flex row gap-10" style="padding-right: 10px">
    <div class="loader"></div><div>Renaming File</div>
    </div>
    `;
    console.log(json);
    document.getElementById('display_options_response').classList.remove('hide');
    socket.emit('rename_file_insights',(json), (response)=>{
        response = JSON.parse(response);
        console.log(response);
        if(check_status_code(response)){
            var display_ = "";
            if(response.error){
                display_ = response.error;
            } else {
                display_ = "File Renamed";
                document.getElementById("overlay").style.display = "none";
            }
            document.getElementById('display_options_response').innerHTML = `
            <div>${display_}</div>
            <div class="flex align-center" onclick="remove_activity_log()">
                <img src="/static?file_name=x-regular-white-24.png">
            </div>
            `;
           
            setTimeout(() => {
                document.getElementById('display_options_response').classList.add('hide');
            }, 5000);
        }
    })
}

function add_file_category_insights(id){
    file_name = document.getElementById('new_file_name_insights').value; 
    category = document.getElementById('new_file_format_category').value;
    console.log(file_name, category);
    
    json = {'drive_id': id, 'name': file_name, 'category' : category};
    document.getElementById('display_options_response').innerHTML = `
    <div class="flex row gap-10" style="padding-right: 10px">
    <div class="loader"></div><div>Formatting File Data</div>
    </div>
    `;
    document.getElementById('display_options_response').classList.remove('hide');
    socket.emit('add_file_category',(json), (response)=>{
        response = JSON.parse(response);
        console.log(response);
        if(check_status_code(response)){
            var display_ = "";
            if(response.error){
                display_ = response.error;
            } else {
                display_ = "Category Added to File";
                document.getElementById("overlay").style.display = "none";
            }
            document.getElementById('display_options_response').innerHTML = `
            <div>${display_}</div>
            <div class="flex align-center" onclick="remove_activity_log()">
                <img src="/static?file_name=x-regular-white-24.png">
            </div>
            `;
           
            setTimeout(() => {
                document.getElementById('display_options_response').classList.add('hide');
            }, 5000);
        }
    });
}
