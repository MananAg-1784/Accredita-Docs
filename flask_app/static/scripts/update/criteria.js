var criteria = [];

function load_acc_criteria(acc = null){
    if(!acc){
        acc= document.getElementById('select_accredition').value;
    }
    loader();
    if(accredition.indexOf(acc) != -1){
        socket_connect();
        socket.emit('criteria-data', {'accredition' : acc}, (response)=>{
            response = JSON.parse(response);
            console.log(response);
            if(check_status_code(response)){
                if(response.error){
                    flash_msg.innerHTML = response.error;
                } else{
                    response = response.response;
                    document.getElementById('acc_data').innerHTML = response.data;
                    criteria = response.criteria;
                    available_cat = response.categories;
                    flash_msg.innerHTML = '';
                    
                    $('#search_criteria').select2({
                        width: '150px'
                    });
                }
            }
        });

    } else{
        flash_msg.innerHTML = 'Invalid Accredition';
    }
}

function refresh_criteria(){
    load_acc_criteria(
        document.getElementById('select_accredition').value
    );
}

function remove_edit_options(child, parent=null){
    if(!parent){
        parent = child.parentNode.parentNode;
    }
    console.log(parent);
    parent.classList.remove('modifying');
    criteria_name = parent.getAttribute('id');
    data = {};
    for(var x of criteria){
        if (x['criteria'] == criteria_name){
            data = x;
        }
    }
    console.log(data);

    parent.querySelector('#edit').innerHTML = 'Edit';
    parent.querySelector('#edit_criteria_button').setAttribute('onclick', 'edit_criteria(this.parentNode)');
    parent.querySelector('#edit_buttons').removeChild(parent.querySelector('#edit_buttons').lastElementChild);
    parent.querySelector('#edit_buttons').removeChild(parent.querySelector('#edit_buttons').lastElementChild);

    parent.querySelector('.criteria_definition').innerHTML = data['definition'];

    var category_list = parent.querySelector('.criteria_category');
    category_list.classList.remove('column');
    category_list.classList.add('row', 'gap-10');
    category_list.innerHTML = '';
    if(data['category'].length < 1){
        category_list.innerHTML = "<em>No Categories Added</em>"
    } else{
        for(var x of data['category']){
            category_list.innerHTML += `<div class="category_name" style="width:fit-content">${x}</div>`;
        }
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
};

function edit_criteria(child){

    var already_editing = document.querySelector('.modifying');
    if(already_editing){
        remove_edit_options(null, already_editing);
    }
    document.getElementById('criteria_options').innerHTML = '';
    parent = child.parentNode.parentNode;
    parent.classList.add('modifying');
    criteria_name = parent.getAttribute('id');
    data = {};
    for(var x of criteria){
        if (x['criteria'] == criteria_name){
            data = x;
        }
    }
    parent.querySelector('.criteria_definition').innerHTML = `
        <textarea name="description" id="description" rows="3" style="width: 300px;">${data['definition'] }</textarea>
    `
    
    var _ = document.createElement('div');
    _.setAttribute('id', 'remove_criteria');
    _.classList.add("flex","row","gap-5","align-center");
    _.setAttribute('onclick', 'remove_criteria(this.parentNode)')
    _.innerHTML = `
    <div class="flex align-center">
        <img src="/static?file_name=trash-regular-24.png" alt="" style="height: 18px !important;">
    </div>
    <div>Delete<div>
    `;
    parent.querySelector('#edit_buttons').appendChild(_);

    var _ = document.createElement('div');
    _.setAttribute('id', 'remove_edit_options');
    _.classList.add("flex","row","gap-5","align-center");
    _.setAttribute('onclick', 'remove_edit_options(this.parentNode)')
    _.innerHTML = `
    <div class="flex align-center">
        <img src="/static?file_name=x-regular-24.png" alt="" style="height: 25px !important; position: relative; top: 1.5px;">
    </div>
    `;
    parent.querySelector('#edit_buttons').appendChild(_);

    parent.querySelector('#edit').innerHTML = 'Modify';
    parent.querySelector('#edit_criteria_button').setAttribute('onclick', 'modify_criteria(this.parentNode)');

    options = [];
    values= [];
    for(var x of available_cat){
        options.push(x['category'] +" - "+ x['definition']);
        values.push(x['category']);
    }

    var category_list = parent.querySelector('.criteria_category');
    category_list.classList.add('column');
    category_list.classList.remove('row','gap-10');
    category_list.innerHTML = `
        <strong>Categories : </strong>
    `;
    var select_t = select_tag(options = options, name='change_category', default_option = 0,onchange_func=null, value = values);
    select_t.setAttribute('id', 'selectMultipleCategory');
    select_t.setAttribute('multiple', "multiple");
    category_list.appendChild(select_t);
    $('#selectMultipleCategory').select2({
        width: '315px',
        placeholder:"Search and Select Category",  
        allowClear: true,
        closeOnSelect: false,
        templateSelection: category_selection_text
    });
    $('#selectMultipleCategory').val(data['category']).trigger('change');
}

function new_criteria(){
    flash_msg.innerHTML = "";

    cat_options = document.getElementById('criteria_options');
    cat_options.style.display = 'flex';
    cat_options.innerHTML =`
    <div class="flex column gap-10">
        <div id="more_options_"></div>
        <div class="flex row gap-25" style="justify-content: space-between;">
            <div style="font-size: 19px; font-weight: 600;">
                Add New Criteria
            </div>
            <div class="flex align-center" onclick="remove_options_for_criteria()" style="cursor: pointer;">
                <img src="/static?file_name=x-regular-24.png" alt="" style="height: 25px;">
            </div>
        </div>
        <div class="flex column gap-10">
            <div class="flex column gap-5">
                <label>Enter Criteria Number </label>
                <input type="text" id="criteria_number">
            </div>
            <div class='flex column gap-5'>
                <label>Description : </label>
                <textarea name="description" id="description" rows="3"></textarea>
            </div>
            <div id='add_categories' class="flex column gap-5">
                <label>Add Categories </label>
            </div>
            <button onclick="add_new_criteria()">Create</button>
        </div>
    </div>
    `
    options = [];
    values= [];
    for(var x of available_cat){
        options.push(x['category'] +" - "+ x['definition']);
        values.push(x['category']);
    }

    var select_t = select_tag(options = options, name='select_category', default_option = 0,onchange_func=null, value = values);
    select_t.setAttribute('id', 'selectMultiple');
    select_t.setAttribute('multiple', "multiple");
    document.getElementById('add_categories').appendChild(select_t);
    $('#selectMultiple').select2({
        width: '350px',
        placeholder:"Search and Select Category",  
        allowClear: true,
        closeOnSelect: false,
        templateSelection: category_selection_text
    });
    $('#selectMultiple').val(null).trigger('change');
}

function add_new_criteria(){
    // Extract all the information for the criteria
    display_prog("<div class='loader'></div><div>Creating...</div>", false);
    var acc= document.getElementById('select_accredition').value;
    data = {
        'criteria' : document.querySelector('#criteria_options #criteria_number').value,
        'definition' : document.querySelector('#criteria_options #description').value,
        'categories' : $('#selectMultiple').val(),
        'accredition' : acc
    };
    console.log(data);
    if(data){
        socket_connect();
        socket.emit('add-criteria', data, (response)=>{
            response = JSON.parse(response);
            console.log(response);
            if(check_status_code(response)){
                if(response.error){
                    display_prog(response.error);
                } else{
                    display_prog("Criteria Created");
                    flash_msg.innerHTML = "";
                    document.getElementById('criteria_options').style.display = 'none';
                    flash_msg.innerHTML = 'Refresh to Fetch Updates..';
            }
        }
        });
    } else{
        display_prog('Missing required fields')
    }
}

function modify_criteria(child){
    console.log("Modifying criteria");
    parent = child.parentNode.parentNode;   
    console.log(parent);
    // Extract all the information for the criteria
    display_prog('<div class="loader"></div><div>Modifying Criteria</div>', false);
    data = {
        'criteria' : parent.querySelector('.criteria .criteria_name').innerHTML,
        'definition' : parent.querySelector('.criteria #description').value,
        'categories' : $('#selectMultipleCategory').val(),
    };
    console.log(data);
    if(data){
        socket_connect();
        socket.emit('modify-criteria', data, (response)=>{
            response = JSON.parse(response);
            console.log(response);
            if(check_status_code(response)){
                if(response.error){
                    display_prog(response.error);
                } else{
                    display_prog("Criteria Modified");
                    console.log("Updated..");
                    document.getElementById('criteria_options').innerHTML = '';
                    load_acc_criteria();
                }
            }
        });
    } else{
        flash_msg.innerHTML = 'Error Try Again';
    }
}


function search_criteria(name){
    var criteria_list = document.querySelectorAll('#criteria_list > div');

    for(var x of criteria_list){
        if(name != 99){
            if(name !== x.getAttribute('id')){
                x.style.display = 'none';
            } else{
                x.style.display = 'flex';
            }
        } else{
            x.style.display = 'flex';
        }
    }
}

function remove_criteria(child){
    parent = child.parentNode.parentNode;   
    console.log(parent);
    var criteria_no = parent.id;
    display_prog('<div class="loader"></div><div>Removing Criteria</div>', false);
    if (criteria_no){
        socket_connect();
        socket.emit('remove-criteria', criteria_no, (response)=>{
            response = JSON.parse(response);
            console.log(response);
            if(check_status_code(response)){
                if(response.error){
                    display_prog(response.error);
                } else{
                    display_prog("Criteria Removed");
                    console.log("Removed..");
                    document.getElementById('criteria_options').innerHTML = '';
                    load_acc_criteria();
                }
            }
        });
    } else{
        console.log(criteria_no, "Criteria not present..");
    }
}