
function remove_options(id, option_name){
    select_ = document.getElementById(id);
    var child = select_.lastElementChild;
    while (child) {
        select_.removeChild(child);
        child = select_.lastElementChild;
    }
}

function add_options(id, options, values=null){
    var select_ = document.getElementById(id);
    var flag = 0;
    for( var x of select_.options){
        if(x.value == 'all'){
            flag = 1;
            console.log("All option present");
            break;
        }
    }
    for (i = 0; i < options.length; i++) {
        if(values){
            let option = new Option(values[i], options[i]);
            select_.add(option, undefined);
        } else{
            let option = new Option(options[i], options[i]);
            select_.add(option, undefined);
        }
    }
    if(flag != 1){
        console.log("All option not present");
        let option = new Option('All', 'all');
        select_.add(option, undefined);
        select_.value= 'all';
    }
}

function add_categories(folder=null){
    options = [];
    values= [];
    console.log("Adding for ...", folder);
    for(x of category){
        if(folder){
            for(var _ of folder){
                if(x.folders.indexOf(_) != -1){
                    if(options.indexOf(x.category) == -1){
                        options.push(x.category);
                        values.push( x.definition+' - '+x.category);
                    }
                }
            }
        } else{ // adding all the categories
            console.log("Adding for all folders");
            options.push(x.category);
            values.push( x.definition+' - '+x.category );
        }
    }
    if(options.length >=1 ){
        console.log(options.length);
        add_options('select_category', options, values);
    } else{
        add_categories();
    }

}

function add_acc_data(acc){
    flash_msg.innerHTML = '';
    // adding folders
    options = [];
    var flag = 0;
    for( var x of folders){
        if(x.accredition == acc){
            options.push(x.folder);
        }
    }
    remove_options('select_folder', 'Select Folder');
    if(options.length >=1 ){
        add_options(id='select_folder', options = options);
    } else{
        console.log("No folders for the accredition");
        flag =1;
    }

    // adding criteria
    acc_criteria = criteria[acc];
    options = [];
    for( var x of acc_criteria){
        options.push(x.criteria);
    }
    remove_options('select_criteria', 'Select Criteria');
    if(options.length >= 1){
        add_options(id='select_criteria', options = options);
    } else {
        flag=2;
    }

    check_options('select_criteria');
    change_category();
    
    if(flag == 1){
        flash_msg.innerHTML= 'No folders associated...';
    } else if(flag == 2) {
        flash_msg.innerHTML = 'No Criterias associated...';
    }
    $("#select_category").val('').trigger("change");
    $("#select_criteria").val('').trigger("change");
}   

function check_options(id){
    select_ = document.getElementById(id);
    var selected_values = $('#'+id).val();
    var flag = 0;
    var options = select_.options;
    if(selected_values.length == 0){
        for(var x of options){
            x.disabled = false;
        }
    } else if(selected_values.length == 1 && selected_values[0] === 'all'){    
        for(var x of options){
            if(x.value !== 'all'){
                x.disabled = true;
            }
        }
        $('#'+id).select2('close');
    } else {
        for(var x of selected_values){
            if(x === 'all' ){
                flag = 1;
                break;
            }
        }
        for(var x of options){
            if(flag == 1){
                if(x.value !== 'all'){
                    x.disabled = true;
                }
            } else{
                x.disabled = false;
            }
        }
        if(flag == 1){
            $('#'+id).val('all').trigger('change');
            $('#'+id).select2('close');
        }
    }
}

function change_category(){
    flash_msg.innerHTML = '';
    check_options('select_folder');
    var selected_folders = $('#select_folder').val();
    
    // add all the categories
    remove_options('select_category', 'Select Category');
    if(selected_folders.length > 0){
        if(selected_folders.length == 1 && selected_folders[0] == 'all'){
            add_categories();
        } else{
            add_categories(selected_folders);
        }
        if( document.getElementById('checked').checked ){
            $("#select_category").val('all').trigger("change");
        } else{
            $("#select_category").val('').trigger("change");
        }
    }
    check_options('select_category');
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

function radio_check(value){
    if(value == 1){
        $("#select_criteria").prop("disabled", true);
        $("#select_criteria").val('').trigger("change");
        $("#select_category").prop("disabled", false);
        $("#select_category").val('all').trigger("change");
    } else {
        $("#select_criteria").prop("disabled", false);
        $("#select_criteria").val('all').trigger("change");
        $("#select_category").val('').trigger("change");
        $("#select_category").prop("disabled", true);
    }
}

$('#select_folder').select2({
    width: '220px',
    placeholder:"Search and Select Folder",  
    closeOnSelect: false,
});
$('#select_criteria').select2({
    width: '220px',
    placeholder:"Search and Select Criteria",  
    closeOnSelect: false
});
$('#select_category').select2({
    width: '220px',
    placeholder:"Search and Select Category",  
    closeOnSelect: false,
    templateSelection: category_selection_text
});
$("#select_criteria").prop("disabled", true);
$("#select_category").prop("disabled", true);

function academic_years(){
    var acc_year = document.getElementById('select_academic_year');
    var acc_mnth = document.getElementById('select_academic_month');
    const d_ = new Date();
    var year = d_.getFullYear();
    var month = d_.getMonth() + 1;

    for (i = 2020; i <= year; i++) {
        year_short = i % 100;
        if( i == year && month < acc_start_mnth){
            console.log("Acadmic year not  yet started for : " + i);
            break;
        }
        else{
            let option = new Option(""+ year_short + "-" + (year_short +1), i);
            acc_year.add(option, undefined);
        }
    }
    acc_year.value = acc_year.lastChild.value;

    for(i=0;i <months.length; i++)
    {
        let option = new Option(months[i], i+1);
        acc_mnth.add(option, undefined);
    }
    acc_mnth.value = (acc_start_mnth).toString();
}

function display_academic_year_details(){
    var display = document.getElementById('academic_year_details');
    var year = parseInt(document.getElementById('select_academic_year').value);
    var month = parseInt(document.getElementById('select_academic_month').value) - 1;
    
    display.innerHTML= `
    Selected : ${months[month]} ${year} to ${months[(month-1+12)%12]} ${year+1}
    `;
}

function change_academic_year(){
    document.getElementById('select_academic_month').value = (acc_start_mnth).toString();
    display_academic_year_details();
}
academic_years();
display_academic_year_details();

