var folder_cat = {};
var cat_list = document.getElementById('category_container');

function refresh_category(){
    load_folder_category_details(
        document.querySelector(".select_folder").value
    );
}

function load_folder_category_details(folder){
    console.log("Loading categories for folder", folder);
    loader('Loading Folder details..');
    document.getElementById('go_back').style.display = "flex";
    
    socket.emit( 'get-folder-cat', {'folder' : folder}, (response)=> {
        response = JSON.parse(response);
        console.log(response);
        if(check_status_code(response)){
            if(response.error){
                location.reload();
            } else {
            response = response.response;
            console.log("Response : ", response);

            document.getElementById('folder_category_details').innerHTML= `
                <div class="flex row gap-25">
                ${response.data}
                </div>
            `;

            available_cat = response.response.available_category;
            folder_cat = response.response.folder_category;

            flash_msg.innerHTML = '';
            display_buffer_changes('add');
            }
        }
    });

}

// removes the parent node and add the categorycode to #delete_cat
function remove_category(childNode){
    cat_list = document.getElementById('category_container');
    cat_list.removeChild(childNode);

    var category_name = childNode.getElementsByClassName('category_name')[0].innerHTML;
    var category_definition = childNode.getElementsByClassName('category_definition')[0].innerHTML;

    delete_cat = document.getElementById('delete_cat');
    cat_ = document.createElement('div');
    cat_.innerHTML = `
        <span class="name">${category_name}</span>
        <span class="definition hide">${category_definition}</span>
        <span style="cursor: pointer;" onclick="add_removed_category(this.parentNode)" style=cursor: pointer; display: flex;">
            <img src="/static?file_name=x-circle-regular-white-24.png" style="height: 20px;">
        </span>
    `;
    delete_cat.appendChild(cat_);
    delete_cat.querySelector('#nothing').classList.add('hide');

    for (var x of folder_cat){
        if( x.category === category_name ){
            folder_cat = folder_cat.filter(item => item.category !== x.category);
            break;
        }
    }

    if(document.querySelectorAll('#category_container > div').length == 0){
        cat_list.innerHTML = `<div style="font-size: 18px; height: 58vh; font-style: italic;">No Categories Added to the Folder</div>`;
    }
}

function add_category(){
    document.getElementById('category_options').style.display = 'none';
    var category_selected = $('.select_category').val();
    console.log(category_selected);
    var category = {};

    document.getElementById('category_options').innerHTML = '';

    for(var category_name of category_selected){
        for (var x of available_cat){

            if( x.category === category_name ){
                category = x;
                available_cat = available_cat.filter(item => item.category != x.category);
                folder_cat.push(category);
                break;
            }
        }
        console.log(category);
        // add the category in the #add_cat
        add_cat = document.getElementById('add_cat');
        cat_ = document.createElement('div');
        cat_.innerHTML = `
            <span class="name">${category.category}</span>
            <span class="definition hide">${category.definition}</span>
            <span style="cursor: pointer;" onclick="remove_added_category(this.parentNode)" style=cursor: pointer; display: flex;">
                <img src="/static?file_name=x-circle-regular-white-24.png" style="height: 20px;">
            </span>
        `;
        add_cat.appendChild(cat_);

    }
    add_cat.querySelector('#nothing').classList.add('hide');
}

function add_removed_category(parent){
    var category_name = parent.querySelector('.name').innerHTML;
    var category_definition = parent.querySelector('.definition').innerHTML;

    document.getElementById('delete_cat').removeChild(parent);

    folder_cat.push( {'category': category_name, 'definition': category_definition} );

    var cat_ = document.createElement('div');
    cat_.setAttribute('id' , 'category_');
    cat_.classList.add('flex','row','gap-10', 'align-center');

    cat_.innerHTML = `
        <div class="flex row gap-10">
            <span class="category_name">${category_name}</span>
            <span>|</span>
            <span class="category_definition cut-text">${category_definition}</span>
        </div>
        <div onclick="remove_category(this.parentNode)" class="flex align-center" style="cursor: pointer;">
            <img src="/static?file_name=x-circle-regular-white-24.png">
        </div>
    `;

    if(cat_list.firstElementChild.innerHTML == "No Categories Added to the Folder"){
        cat_list.removeChild(cat_list.firstElementChild);
    }

    cat_list.appendChild(cat_);
    console.log('Available category : ', available_cat);
    console.log('Folder categories : ', folder_cat);

    if(document.getElementById('delete_cat').childElementCount <= 1){
        document.getElementById('delete_cat').querySelector('#nothing').classList.remove('hide');
    }
}

function remove_added_category(parent){
    var category_name = parent.querySelector('.name').innerHTML;
    var category_definition = parent.querySelector('.definition').innerHTML;

    document.getElementById('add_cat').removeChild(parent);
    category = {'category' : category_name, 'definition': category_definition};

    if(document.getElementById('add_cat').childElementCount <= 1){
        document.getElementById('add_cat').querySelector('#nothing').classList.remove('hide');
    }

    available_cat.push(category);
    folder_cat = folder_cat.filter(item => item.category != category.category);

    console.log('Available category : ', available_cat);
    console.log('Folder categories : ', folder_cat);
}

function display_buffer_changes(value){
    if(value === 'add'){
        document.getElementById('add_cat_').classList.remove('hide');
        document.getElementById('delete_cat_').classList.add('hide');
        document.getElementById('display_buffer_a').classList.add('show_buffer');
        document.getElementById('display_buffer_d').classList.remove('show_buffer');
    } else if(value === 'delete'){
        document.getElementById('delete_cat_').classList.remove('hide');
        document.getElementById('add_cat_').classList.add('hide');
        document.getElementById('display_buffer_d').classList.add('show_buffer');
        document.getElementById('display_buffer_a').classList.remove('show_buffer');
    }
}

// add a select for adding new cat inside the #category_list
// append the cat in the #add_cat
function add_category_options(){
    var cat_options = document.getElementById('category_options');
    cat_options.style.display = 'flex';
    cat_options.innerHTML = `
        <div class="flex column gap-10">
            <div id="more_options_"></div>
            <div class="flex row gap-25" style="justify-content: space-between;">
                <div style="font-size: 19px; font-weight: 600;">
                Add Categories to the Folder
                </div>
                <div class="flex align-center" onclick="remove_options_for_category()" style="cursor: pointer;">
                    <img src="/static?file_name=x-regular-24.png" alt="" style="height: 25px;">
                </div>
            </div>
            <div class="flex column gap-10">
                <div class="flex column gap-15" id="add_category_disp_">
                </div>
                <button onclick="add_category()" id="add_new_cat" style="background-color: grey; border-color:darkgrey;" disabled>
                    Add List
                </button>
            </div>
        </div>
    `;
    var options=[];
    var values=[];
    for(var x of available_cat){
        options.push(x['category'] +" - "+ x['definition']);
        values.push(x['category']);
    }

    var select_t = select_tag(options = options, name='select_category', default_option = 'Select Category', onchange='enable_add_cat(this.value, -1)', value = values);
    select_t.setAttribute('multiple', "multiple");
    select_t.setAttribute('id', 'selectSearch');
  
    document.getElementById('add_category_disp_').appendChild(select_t);
    $('#selectSearch').select2({
        width: '340px',
        placeholder:"Select Categories",  
        allowClear: true,
        closeOnSelect: false,
        templateSelection: category_selection_text
    });
    $('#selectSearch').val(null).trigger('change');
}

function create_category_options(){
    var cat_options = document.getElementById('category_options');
    cat_options.style.display="flex";

    cat_options.innerHTML = `
    <div class="flex column gap-10">
        <div id="more_options_"></div>
        <div class="flex row gap-25" style="justify-content: space-between;">
            <div style="font-size: 19px; font-weight: 600;">
            Add New Category
            </div>
            <div class="flex align-center" onclick="remove_options_for_category()" style="cursor: pointer;">
                <img src="/static?file_name=x-regular-24.png" alt="" style="height: 25px;">
            </div>
        </div>
        <div class="flex column gap-10">
            <div class="flex column gap-5">
                <label for="new_category_name">Name of the Category (4-5 letter only)</label>
                <input type="text" name="new_category_name" id="new_category_name" placeholder="Enter the category code">
            </div>
            <div class='flex column gap-5'>
                <label for="new_category_definition">Definition</label>
                <textarea name="new_category_definition" id="new_category_definition" rows="3"
                placeholder="Enter category definition"></textarea>
            </div>
            <button onclick="add_new_category()" id="add_new_cat">Create</button>
        </div>
    </div>
    `;
    enable_add_cat(1, -1);
}

function modify_category_options(){
    flash_msg.innerHTML = '';
    var cat_options = document.getElementById('category_options');
    cat_options.style.display="flex";

    cat_options.innerHTML = `
    <div class="flex column gap-10">
        <div id="more_options_"></div>
        <div class="flex row gap-25" style="justify-content: space-between;">
            <div style="font-size: 19px; font-weight: 600;">
                Modify Category
            </div>
            <div class="flex align-center" onclick="remove_options_for_category()" style="cursor: pointer;">
                <img src="/static?file_name=x-regular-24.png" alt="" style="height: 25px;">
            </div>
        </div>
        <div class="flex column gap-15" id="modify_category_disp_">
            <div class="flex column gap-5">
                <label for="new_category_name">Select the category to modify</label>
            </div>
        </div>
    </div>
    `;
    var options=[];
    var values=[];
    for(var x of available_cat){
        options.push(x['category'] +" - "+ x['definition']);
        values.push(x['category']);
    }

    var select_t = select_tag(options = options, name='select_category', default_option = 'Select Category', onchange='change_definition(this.value)', value = values);
    select_t.setAttribute('id', 'selectSearch');
    document.getElementById('modify_category_disp_').firstElementChild.appendChild(select_t);
    $('#selectSearch').select2({
        width: '350px'
    });

}

function delete_category_options(){
    flash_msg.innerHTML = '';
    var cat_options = document.getElementById('category_options');
    cat_options.style.display="flex";

    cat_options.innerHTML = `
    <div class="flex column gap-10">
        <div id="more_options_"></div>
        <div class="flex row gap-25" style="justify-content: space-between;">
            <div style="font-size: 19px; font-weight: 600;">
                Delete Category
            </div>
            <div class="flex align-center" onclick="remove_options_for_category()" style="cursor: pointer;">
                <img src="/static?file_name=x-regular-24.png" alt="" style="height: 25px;">
            </div>
        </div>
        <div class="flex column gap-15" id="modify_category_disp_">
            <div class="flex column gap-5">
                <label for="new_category_name">Select the category to Delete</label>
            </div>
        </div>
        <button onclick="delete_category()" id="add_new_cat">
            Delete
        </button>
    </div>
    `;
    var options=[];
    var values=[];
    for(var x of available_cat){
        options.push(x['category'] +" - "+ x['definition']);
        values.push(x['category']);
    }

    var select_t = select_tag(options = options, name='select_category', default_option = 'Select Category', onchange='', value = values);
    select_t.setAttribute('id', 'delete_category_select');
    document.getElementById('modify_category_disp_').firstElementChild.appendChild(select_t);
    $('#delete_category_select').select2({
        width: '350px'
    });
}

// extract the code and the definition of the category from the select statement

function change_definition(value){
    var cat_options = document.getElementById('modify_category_disp_');
    if(cat_options.childElementCount == 2){
        cat_options.removeChild(cat_options.lastElementChild);
    }
    var category = {};
    for(var x of available_cat){
        if(value == x['category']){
            category = x;
            break;
        }
    }
    var _text = document.createElement('div');
    _text.classList.add("flex" ,"column" ,"gap-5");
    _text.innerHTML = `    
            <div class="flex row gap-5" style="font-weight:600;"> 
               <span>Category code : </span> 
               <span id="category_name">${category.category}</span> 
            </div>
            <div class="flex column gap-5"> 
                <label for="new_category_definition">Definition :</label>
                <textarea name="new_category_definition" id="new_category_definition" rows="3"
                placeholder="Enter category definition" style="width: 340px !important;">${category.definition}</textarea> 
            </div>
            <button id="add_new_cat" onclick="modify_old_category('${category.category}', '${category.definition}')">
                Modify
            </button>
    `;
    cat_options.appendChild(_text);
    enable_add_cat(value, -1);
}

function enable_add_cat(value, match_value){
    button_=  document.getElementById('add_new_cat');
    if(value != match_value){
        button_.disabled = false;
        button_.style.backgroundColor = '#0d6efd';
        button_.style.borderColor = '#0d6efd';
    } else{
        button_.disabled = true;
        button_.style.backgroundColor = 'xzgrey';
        button_.style.borderColor = 'grey';
    }
}


// get the code and defitnition
// check if that code exists if not add new code and refresh the page add that code the folder
function add_new_category(){
    var category_name = document.getElementById('new_category_name').value;
    var category_def = document.getElementById('new_category_definition').value; 
    var folder = document.querySelector('.select_folder').value;
    console.log("Creting category .. ", category_name, category_def, folder);
    if( category_name != '' && category_def != '' ){
        var json = {'folder' : folder, 'name': category_name, 'def': category_def };
        display_prog("<div class='loader'></div><div>Creating...</div>", false);
        socket_connect();
        socket.emit('add-new-category', json, (response)=>{
            response = JSON.parse(response);
            console.log(response);
            flash_msg.innerHTML = '';
            if(check_status_code(response)){
                if(response.error){
                    display_prog(response.error);
                } else {
                    console.log(folder);
                    flash_msg.innerHTML = 'Refresh to Fetch Updates..';
                    document.getElementById('category_options').style.display = 'none';
                    display_prog("Category Created");
                    available_cat = response.response;
                }
            }
        });
    }
}

// extracts the name and def of the category to be modified
// pass data_dict[user_id] for getting the dept in the socket
function modify_old_category(category_name, category_definition){

    flash_msg.innerHTML = '';
    var new_cat_def = document.getElementById('new_category_definition').value;

    if(new_cat_def != '' && new_cat_def !== category_definition){
        
        display_prog("<div class='loader'></div><div>Updating...</div>", false);
        json = {'category' : category_name, 'definition': new_cat_def};
        socket_connect();
        socket.emit('modify_old_category', json, (response)=>{
            response = JSON.parse(response);
            console.log(response);
            if(check_status_code(response)){
                if(response.error){
                    display_prog(response.error);
                } else {
                    console.log(folder);
                    flash_msg.innerHTML = 'Refresh to Fetch Updates..';
                    document.getElementById('category_options').style.display = 'none';
                    display_prog("Category Updated");
                    available_cat = response.response;
                }
            }
        })

    }
}

function delete_category(){
    var cat_to_del = document.getElementById('delete_category_select').value;
    console.log(cat_to_del);

    display_prog('<div class="loader"></div><div>Removing Category</div>', false);
    if (cat_to_del){
        socket_connect();
        socket.emit('delete-category', cat_to_del, (response)=>{
            response = JSON.parse(response);
            console.log(response);
            if(check_status_code(response)){
                if(response.error){
                    display_prog(response.error);
                } else{
                    display_prog("Category Removed");
                    console.log("Removed..");
                    document.getElementById('category_options').style.display = 'none';
                    available_cat = response.response;
                }
            }
        });
    } else{
        console.log(cat_to_del, "Criteria not present..");
    }
}

// submits the category changes from the #changed_category
// refreshed the category list for the folder load_folder_category_details(folder_name)
function submit_category_list(){
    console.log('Categories to be added = ', folder_cat);
    var categories = [];
    for(var x of folder_cat){
        categories.push(x.category);
    }
    console.log(categories);
    folder = document.querySelector('.select_folder').value;
    data = {'folder': folder, 'categories' : categories};

    display_prog('<div class="loader"></div>Updating</div>', false);
    socket_connect();

    socket.emit('modify-category', data, (response)=>{
        response = JSON.parse(response);
        console.log(response);
        if(check_status_code(response)){
            flash_msg.innerHTML = '';
            if(response.error){
                display_prog(response.error);
            } else{
                display_prog("Categories Updated");
                load_folder_category_details(folder);
            }
        }
    });
}