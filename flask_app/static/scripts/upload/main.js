

const dropArea = document.querySelector(".drop_box"),
button = dropArea.querySelector("button"),
dragText = dropArea.querySelector("header"),
input = dropArea.querySelector("input");
var get_activity = 1;

button.onclick = () => {
  input.click();
};

var files_uploaded = {}
var files_list = {};
var data_item = 0;
var activity_file_data_list = {};

input.addEventListener("change", function (e) {
  flash_msg.innerHTML = '';
  console.log("Adding File data");
  var files = e.target.files;
  console.log(files_list);
  for( var x of files ){
    // check is file already added or not
    flag = 0;
    for(var _ in files_list){
        if(files_list[_].name === x.name && files_list[_].size === x.size && files_list[_].type === x.type){
            flag = 1
        }
    }
    for(var _ in files_uploaded){
        if(files_uploaded[_].name === x.name && files_uploaded[_].size === x.size && files_uploaded[_].mimeType === x.type){
            flag = 1
        }
    }
    if(flag == 0){
        files_list[data_item] = x;
        display_file_data(data_item);
        data_item += 1;
    } else{
        console.log('Cannot add data');
        flash_msg.innerHTML += `
            <div class="flex gap-5">
                <span class="cut-text" style="display:inline-block; font-weight: 400; color: black;">${x.name}</span> 
                <span>already added..</span>
            </div>
            `
    }
  }
});

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

function formatFileSize(bytes, sizeLimitIgnore = false) {
    if (bytes === 0) return '0 Bytes';

    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];

    const i = Math.floor(Math.log(bytes) / Math.log(k));
    var val = parseFloat((bytes / Math.pow(k, i)).toFixed(2));4
    if(!sizeLimitIgnore){
        if(val > 200 && i==2){
            return null;
        }
    }
    return val + ' ' + sizes[i];
}

function display_file_data(item_no){
    var file_name = files_list[item_no].name;
    var file_type = files_list[item_no].type;
    var file_size = formatFileSize(files_list[item_no].size);
    var icon = mimeTypes[file_type] ?? "/static?file_name=file-regular-24.png";

    var container = document.createElement('div');
    container.classList.add('file_data', 'column', 'gap-10', 'flex');
    container.setAttribute('id', `data_item_${item_no}`);
    var html_data = `    
        <div class="flex row align-center" style="font-size: 17px;">
            <div class="flex row gap-10">
              <div class="flex align-center" style="cursor: pointer;" onclick="remove_file(${item_no})">
                <img src="/static?file_name=x-regular-24.png" alt="">
              </div>
              <div class="flex"><img src="${icon}" alt=""></div>
              <div class="cut-text">
              <abbr title="${file_name}">${file_name}</abbr>s
              </div>
            </div>

            <div class="flex row gap-5">
              <span>File Size :</span>
              <span>${file_size}</span>
            </div>
        </div>
        
        <div class="flex row align-center">
            <div class="flex row align-center gap-10">
                <div class="flex align-center">
                    <img src="/static?file_name=x-regular-24.png" alt="" style="visibility:hidden;">
                </div>
                <div class="flex row gap-15"> 
                    <select name="select_category" class="file_category" multiple = "multiple" onchange="add_details(${item_no})">
                    </select>
                    <input class="form_input" id="new_file_name" type="file_name" placeholder="Enter File Name">
                </div>
            </div>
            
            <div class="flex row align-center" id="more_options" onclick="display_more_options(${item_no})">
              <span>More Options</span>
              <div>
                <img src="/static?file_name=arrow_head.png" alt="">
              </div>
            </div>
        </div>

        <div class="flex row align-center" id="more_options_data">
            <div class="flex row align-center gap-10">
                <div class="flex align-center">
                    <img src="/static?file_name=x-regular-24.png" alt="" style="visibility:hidden;">
                </div>
                <div class="flex row gap-15"> 
                    <select name="select_folder" class="file_folder" multiple = "multiple">
                    </select>
                </div>
            </div>
        </div>
    `;

    if(file_size == null){
        file_size = formatFileSize(files_list[item_no].size, true);
        html_data = `
        <div class="flex row align-center" style="font-size: 17px;">
            <div class="flex row gap-10">
                <div class="flex align-center"  style="cursor: pointer;" onclick="remove_file(${item_no})">
                    <img src="/static?file_name=x-regular-24.png" alt="">
                </div>
                <div class="flex"><img src="${icon}" alt=""></div>
                <div class="cut-text" style="font-weight: bold;">${file_name} size is greater than 200MB</div>
            </div>
            
            <div class="flex row gap-5">
                <span>File Size :</span>
                <span>${file_size}</span>
            </div>
        </div>
        `;
    }
    container.innerHTML = html_data;
    document.getElementById('upload_file_data').appendChild(container);
    
    file_size = formatFileSize(files_list[item_no].size);
    if(file_size != null){
        var select_ = '#data_item_'+item_no+' .file_folder';
        $(select_).select2({
            width: '250px',
            closeOnSelect: true,
            alowClear: true,
            placeholder: 'Select Folders',
            templateSelection: category_selection_text
        });
        $(select_).val('').trigger('change');
        for (var i of available_folders) {
            let option = new Option(i,i);
            document.querySelector(select_).add(option, undefined);
        }
        var select_ = '#data_item_'+item_no+' .file_sub_folder';
        $(select_).select2({
            width: '250px',
            closeOnSelect: true,
            alowClear: true,
            placeholder: 'Select Sub Folder',
            templateSelection: category_selection_text
        });
        $(select_).val('').trigger('change');
        add_categories(item_no);
        // display_more_options(item_no);
    } else{
        delete files_list[item_no];
    }
}

function category_selection_text(state){
    if (!state.id) {
        return state.text;
    } else if(state.id == 'all'){
        return state.text;
    } else{
        return state.id;
    }
}

function add_categories(item_no){
    var select_ = '#data_item_'+item_no+' .file_category';
    $(select_).select2({
        width: '250px',
        closeOnSelect: true,
        alowClear: true,
        placeholder: 'Select file Category',
        templateSelection: category_selection_text
    });
    $(select_).val('').trigger('change');

    select_ = document.querySelector(select_);
    options = [];
    values= [];
    console.log("Adding all categories");
    for(x of category){
        options.push(x.category);
        values.push( x.definition+' - '+x.category );
    }
    if(options.length >=1 ){
        console.log(options.length);
        for (i = 0; i < options.length; i++) {
            let option = new Option(values[i], options[i]);
            select_.add(option, undefined);
        }
    } else{
        flash_msg.innerHTML = 'Reload and Try Again...';
    }
}

function get_date(){
    const d = new Date();
    year = d.getFullYear();
    month = d.getMonth() + 1;
    date = d.getDate();
    var format_date = '' + year;
    if (month < 10)
        format_date = format_date + '0' + month;
    else
        format_date = format_date + month;
    if (date < 10)
        format_date = format_date + '0' + date;
    else
        format_date = format_date + date;
    return format_date;
}

function add_file_name(item_no, category_){
    var new_file_name = get_date();
    var cat_  = '';
    for(var x of category_){
        cat_ += x +',';
    }
    if(cat_.length == 0){
        return
    }
    new_file_name +='_'+ cat_.slice(0,cat_.length-1) + '_';
    new_file_name += files_list[item_no].name;

    _ = document.querySelector(`#data_item_${item_no} #new_file_name`);
    console.log(_);
    try{
        _.value = new_file_name;
    } catch {
        console.log();
    }
}

// add the folders for the category and filename
function add_details(item_no){
    flash_msg.innerHTML = '';
    item = document.getElementById(`data_item_${item_no}`);
    folder_ = item.querySelector('.file_folder');
    categories = $(`#data_item_${item_no} .file_category`).val();
    if(categories == null){
        return
    }

    // getting the folders to be added
    options = [];
    for(var x of category){
        if(categories.includes(x.category) ){
            for(var _ of x.folders){
                if( !options.includes(_) ){
                    options.push(_);
                }
            }
        }
    }
    // adding new options
    if(options.length >=1 ){
        $(folder_).val(options).trigger('change');
    } 
    add_file_name(item_no, categories);
}

function remove_file(item_no){
    flash_msg.innerHTML = '';
    item = document.getElementById(`data_item_${item_no}`);
    delete files_list[item_no];
    document.getElementById('upload_file_data').removeChild(item);
}

function display_more_options(item_no)
{
    flash_msg.innerHTML = '';
    var data_item = document.getElementById(`data_item_${item_no}`);
    var classList_ = data_item.querySelector('#more_options_data').classList;
    if(classList_.contains('hide')){
        classList_.remove('hide');
    } else{
        classList_.add('hide');
    }
}

function add_uploading_file(file_data, item_no){
    document.getElementById('files_uploading').classList.remove('hide');
    div_ = document.createElement('div');
    div_.classList.add('flex', 'column', 'gap-15', 'uploading_file_data');
    div_.setAttribute('id', `uploading_${item_no}`);
    var icon = mimeTypes[file_data.mimeType] ?? "/static?file_name=file-regular-24.png";

    var _folders = '';
    for(var x of file_data.folders){
        _folders += x + ', '; 
    }
    _folders = _folders.slice(0, -2);
    html_data = `
    <div class="flex column gap-5">
        <div class="flex row" style="justify-content: space-between;">
            <div class="flex row gap-5">
                <div class="flex"><img src="${icon}" alt="" style="width: 22px;
                height: auto;"></div>
                <div class="cut-text" style="max-width: 250px !important">
                    <abbr title="${file_data.name}">${file_data.name}</abbr>
                </div>
            </div>
            <div>Size : ${formatFileSize(file_data.size)}</div>
        </div>
        <div style="font-style:italic;">
            Folders : ${_folders}
        </div>
    </div>
    <div class="flex column gap-10" style="width: 100%; margin: 0px;" id="progress">
        <div class="flew column" id="progress_bar">
            <div class="flex row" style="border-radius: 3px; overflow: hidden;">
                <div class="upload_meter" id="already_uploaded"></div>
                <div class="upload_meter" id="pending_upload"></div>
            </div>
            <div style="align-self: flex-start; font-size: 14px; color: grey;">
                <span id="progress_percent">0</span>
                <span> / ${formatFileSize(file_data.size)}</span>
            </div>
        </div>
        <div id="progress_display" style="gap:6px;" class="flex row transfer">
            <div class="progress_loader"></div>
            <div id="display_progresses" class="cut-text" style="max-width: 250px !important">Uploading the File</div>
        </div>
    </div>
    `;
    div_.innerHTML = html_data;
    document.getElementById('uploading_data').appendChild(div_);
}

function upload_files(){
    flash_msg.innerHTML = '';
    for(var x in files_list){
        var _ = document.getElementById(`data_item_${x}`);
        var name = _.querySelector('#new_file_name').value;
        var categories = $(`#data_item_${x} .file_category`).val();
        var folders = $(`#data_item_${x} .file_folder`).val();
        var sub_folder = $(`#data_item_${x} .file_sub_folder`).val();

        if(name == 0 || categories == 0 || folders == 0){
            d_ = document.createElement('div');
            d_.classList.add('flex','gap-5','row')
            d_.innerHTML = `<div style="font-weight: 400; color: black;">Required fields missing for file : </div><div class="cut-text">${files_list[x].name}</div>`;
            flash_msg.appendChild(d_);
        } else{
            // connect the socket and transfer files one by one
            // remove the file detail from the file to be uploaded and add above in upload meter...

            // check if the file is already uploaded or not
            flag = 0
            for(var z in files_uploaded){
                var _ = files_uploaded[z];
                if(_.name === name && _.size === files_list[x].size && _.mimeType === files_list[x].type ){
                    flag = 1
                    flash_msg.innerHTML += `
                    <div class="flex gap-5" style="font-weight: 400;">
                        <span class="cut-text" style="display:inline-block;">${_.name }</span> 
                        <span>already uploaded...</span>
                    </div>`;
                }
            }
            if(flag == 0){
                file_data = {
                    itemNo: x,
                    name: name,
                    size: files_list[x].size,
                    mimeType: files_list[x].type
                }
                if(sub_folder != 0){
                    file_data['sub_folder'] = sub_folder;
                }
                files_uploaded[x] = file_data;
                
                file_data['categories'] = categories ;
                file_data['folders'] = folders ;
                add_uploading_file(file_data, x); 

                file_data['data'] = files_list[x];
                remove_file(x);
                uploading_files.push(file_data);
            }
        }
    }
    upload_file_data();
}

function display_activity(){
    document.getElementById('activity_display_button').classList.add('hide');
    document.getElementById('activity_data').classList.remove('hide');
    document.getElementById('upload_files').classList.add('hide');
    document.getElementById('files_uploading').classList.add('hide');
    if(get_activity == 1){
        load_activity();
        get_activity += 1;
    }
}

function reset_activity(){
    document.getElementById('activity_display_button').classList.remove('hide');
    document.getElementById('activity_data').classList.add('hide');
    document.getElementById('upload_files').classList.remove('hide');
    if (document.getElementsByClassName('uploading_file_data').length >0){
        document.getElementById('files_uploading').classList.remove('hide');
    }
}


function load_activity(){
    console.log("Loading activity...");
    flash_msg.innerHTML = '<div class="loader"></div><div>Loading Recent Activities...</div>';
    if(!socket.connected){
        socket.connect();
    }  
    socket.emit('load_activity',1,(response)=>{
        response = JSON.parse(response);
        console.log(response);
        if(check_status_code(response)){
            if(response.error){
                flash_msg.innerHTML = response.error;
            } else {
                document.getElementById('activity_details').innerHTML = response.response.html_data;
                activity_file_data_list = response.response.data;
            }
        }
    });
}

function display_activity_files(value){
    var x_ = document.getElementsByClassName('file_activity_data');
    for(var x of x_){
        var c = x.classList;
        if(value === 'restored'){
            if(c.contains('restored')){
                x.classList.remove('hide');
            } else{
                x.classList.add('hide');
            }
        } else if(value === 'trashed'){
            if(c.contains('trashed')){
                x.classList.remove('hide');
            } else{
                x.classList.add('hide');
            }
        } else if(value === 'uploaded'){
            if(c.contains('uploaded') || c.contains('created') || c.contains('copied') ){
                x.classList.remove('hide');
            } else{
                x.classList.add('hide');
            }
        } else{
            x.classList.remove('hide');
        }
    }

    var folders_ = document.getElementsByClassName('folder_data');
    for(var folder_ of folders_){
        if(value == 'all'){
            folder_.classList.remove('hide');
        } else { 
            if(folder_.querySelector('.no_data')){
                folder_.classList.add('hide');
            } else {
                var files_ = folder_.querySelectorAll('.file_activity_data');
                var count= 0;
                for(var x of files_){
                    if(x.classList.contains('hide')){
                        count ++;
                    }
                }
                if(count == files_.length){
                    folder_.classList.add('hide');
                } else {
                    folder_.classList.remove('hide');
                }
            }
        }   
    }
}

function remove_activity_log(){
    document.getElementById('display_options_response').innerHTML = '';
    document.getElementById('display_options_response').classList.add('hide');
}

function rename_file(data_item, name){
    display_ = document.getElementById('overlay');
    display_.style.display = 'flex';
    display_.innerHTML = `
    <div class="flex column gap-10">
        <div class="flex row gap-25" style="justify-content: space-between;">
            <div style="font-size: 19px; font-weight: 600;">
             Renaming the File
            </div>
            <div class="flex align-center" onclick="remove_options_for_overlay()" style="cursor: pointer;">
                <img src="/static?file_name=x-regular-24.png" alt="" style="height: 25px;">
            </div>
        </div>
        <div class="flex column gap-15">
            <div class="flex column gap-5" id="new_file_name_">
                <div>Change or Add File Name</div>
                <input type="text" name="renamed_file" id="renamed_file" placeholder="New File Name" style="width: 340px; font-size:16px;">
            </div>
            <div class="flex column gap-5" id="add_category_disp_options">
            <div>Add Category to the file</div>
            <select id="select_renamed_category" onchange="rename_file_name('${name}')" multiple="multiple" style="width: 250px;">
            </select>
            </div>
            <div class="flex row gap-15">
                <div style="padding: 4px 10px;background-color: #0d6efd;color: #fff;align-self: flex-start;border-radius: 5px; cursor:pointer;" onclick="rename_file_submit('${data_item}','${name}')">
                    Rename File
                </div>
            </div>
        </div>
    </div>
    `;
    document.getElementById('renamed_file').value = name;
    select_ = document.querySelector("#select_renamed_category");
   
    $(select_).select2({
        width: '340px',
        closeOnSelect: true,
        alowClear: true,
        placeholder: 'Select new file Category',
        templateSelection: category_selection_text
    });
   
    options = [];
    values= [];
    console.log("Adding all categories");
    for(x of category){
        options.push(x.category);
        values.push( x.definition+' - '+x.category );
    }
    if(options.length >=1 ){
        console.log(options.length);
        for (i = 0; i < options.length; i++) {
            let option = new Option(values[i], options[i]);
            select_.add(option, undefined);
        }
    } else{
        flash_msg.innerHTML = 'Reload and Try Again...';
    }

    $(select_).val('').trigger('change');
}

function rename_file_name(name){
    name_ = document.getElementById('renamed_file').value;
    let parts = name_.split(/_/);
    console.log(parts);
    categories = $(`#select_renamed_category`).val();
    console.log(categories);
    if(categories == null || categories.length == 0){
        document.getElementById('renamed_file').value = name;
        return
    }

    var cat_  = '';
    for(var x of categories){
        cat_ += x +',';
    }
    name_ = parts[0]+'_'+ cat_.slice(0,cat_.length-1);
    for(var _ = 2; _ < parts.length; _++){
        name_ += '_'+parts[_]
    }
    console.log(name_)

    document.getElementById('renamed_file').value = name_;
}

function remove_options_for_overlay(){
    document.getElementById("overlay").style.display = 'none';
}


function rename_file_submit(data_item,name){
    console.log("item_no : ", data_item);
    var drive_id = activity_file_data_list[data_item];
    console.log(drive_id);

    new_name = document.getElementById('renamed_file').value;
    categories = $(`#select_renamed_category`).val();

    console.log(new_name);
    console.log(categories);
    json = {'drive_id': drive_id, 'name':name,'new_name': new_name, 'categories': categories};
    document.getElementById('display_options_response').classList.remove('hide');
    document.getElementById('display_options_response').innerHTML = `
    <div class="flex row gap-10" style="padding-right: 10px">
    <div class="loader"></div><div>Renaming File</div>
    </div>
    `;
    socket.emit('rename_file',(json), (response)=>{
        response = JSON.parse(response);
        console.log(response);
        if(check_status_code(response)){
            var display_ = "";
            if(response.error){
                display_ = response.error;
            } else {
                display_ = response.response;
                document.getElementById('overlay').style.display = 'none';
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

function restore_file(data_item, folder){
    var drive_id = activity_file_data_list[data_item];
    json = {'drive_id': drive_id, 'folder':folder};
    document.getElementById('display_options_response').classList.remove('hide');
    document.getElementById('display_options_response').innerHTML = `
    <div class="flex row gap-10" style="padding-right: 10px">
    <div class="loader"></div><div>Restoring File</div>
    </div>
    `;
    socket.emit('restore_file',(json), (response)=>{
        response = JSON.parse(response);
        console.log(response);
        if(check_status_code(response)){
            var display_ = "";
            if(response.error){
                display_ = response.error;
            } else {
                display_ = response.response;
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

function delete_file(data_item, action){
    var drive_id = activity_file_data_list[data_item];
    // delete the file forever
    if(action === 'trashed'){
        action = 'delete';
        document.getElementById('display_options_response').innerHTML = `
        <div class="flex row gap-10" style="padding-right: 10px">
        <div class="loader"></div><div>Deleting File</div>
        </div>
        `;
    } else{
        // move the file to trash 
        action = 'trash';   
        document.getElementById('display_options_response').innerHTML = `
        <div class="flex row gap-10" style="padding-right: 10px">
        <div class="loader"></div><div>Trashing File</div>
        </div>
        `;
    }
    json = {'drive_id': drive_id, 'action': action};
    document.getElementById('display_options_response').classList.remove('hide');
    socket.emit('delete_file',(json), (response)=>{
        response = JSON.parse(response);
        console.log(response);
        if(check_status_code(response)){
            var display_ = "";
            if(response.error){
                display_ = response.error;
            } else {
                display_ = response.response;
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


function add_sub_folders(item_no){
    item = document.getElementById(`data_item_${item_no}`);
    console.log(item);
}