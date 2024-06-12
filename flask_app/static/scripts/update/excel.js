var file_input = document.getElementById("fileInput");

function enable_button(){
    var file = file_input.files;
    //enable upload button
    var button_ = document.getElementById('upload_file_button');
    if(file.length > 0){
        button_.disabled = false;
        button_.classList.remove("unselected");
    } else{
        button_.disabled = true;
        button_.classList.add("unselected");
    }
}

function add_excel(){
    flash_msg.innerHTML = '';
    var cat_options = document.getElementById('category_options');
    cat_options.style.display = 'flex';    
    cat_options.innerHTML = `
    <div class="flex column " style="gap:18px;">
        <div class="flex row gap-25" style="justify-content: space-between;">
            <div style="font-size: 19px; font-weight: 600;">
            Uptaing Folder categories using Excel
            </div>
            <div class="flex align-center" onclick="remove_options_for_category()" style="cursor: pointer;">
                <img src="/static?file_name=x-regular-24.png" alt="" style="height: 25px;">
            </div>
        </div>

        <div id="instructions" class="flex column" style="gap:7.5px;">
            <div style=" font-weight: 500; font-size: 17px;">
                Please follow the instructions as given below : 
            </div>
            <ul style="gap:1px; margin-left: 5px; font-size: 16.5px;" class="flex column">
                <li>1. The file should be an <strong>Excel (.xlsx)</strong> file</li>
                <li>2. The file size limit is <strong>50MB</strong>.</li>
                <li>3. Please make sure to <strong>add the Folders</strong> prior to uploading the file.</li>
                <li>4. Check the format of your excel file before uploading : 
                    <ul style="padding-left: 20px; padding-top:3px;">
                        <li><strong>a. Serial no :</strong> Serial Numbering of the rows</li>
                        <li><strong>b. Category :</strong> The Category letter code
                            <em>(All available categories can be downloaded from above)</em></li>
                        <li><strong>c. Definition : </strong>Definition for the category <em>(Can be changed later)</em></li>
                        <li><strong>d. Folder :</strong> Folders for which that particular category needs to be added to</li>
                        <li><em>(In case of more than one folder for a particular category seperate the names using a comma , )</em></li>
                    </ul>  
                </li>
            </ul>
            <div class="flex row gap-10" style="justify-content: space-between; margin-top: 12px;">
                <form action='' methods='' enctype="multipart/form-data" for="fileInput" id="file_form">
                    <label for="fileInput" id="form_label">
                        <input type="file" id="fileInput" accept=".xlsx,.csv" name="files" style="border: none !important;"/>
                    </label>
                </form>
                <button id="upload_file_button" class="unselected" onclick="upload_excel()" style="padding: 5px 9px !important; font-size: 15px;" disabled>Upload File</button>
            </div>
        </div>
        
        <div id="file_upload_response" class="flex column gap-5"> 
        </div>

    </div>
    `;
    file_input = document.getElementById("fileInput");
    file_input.addEventListener("change", enable_button);
}

function upload_excel(){
    // file -- containt list of the files
    // file-data => name, size, type, lastModified
    console.log("Uploading files ...")
    var button_ = document.getElementById('upload_file_button');
    button_.disabled = true;
    button_.classList.add("unselected");
    
    var file = file_input.files[0];
    if( !file.name.endsWith('.xlsx') && !file.name.endsWith('.csv') ){
        display_prog("File is Not An Excel File");
        return
    }
    // limit size if 50MB
    if( file.size > 50*1024*1024){
        display_prog("File size is to Large");
        return
    }
    
    var bytes_read = 0;
    var chunk_size = 1024*100;
    var reader = new FileReader();
    var json_data = {};
    display_prog("<div class='loader'></div><div>Uploading the file</div>");
    
    reader.onload = function (e) {
        if (reader.error) {
            console.error(reader.error);
            display_prog("Error, Try Again");
            return;
        }

        if(reader.readyState != reader.LOADING){
            var data = new Uint8Array(e.target.result);
            json_data.file_data = data;
            
            if(bytes_read == 0){
                json_data.file_name = file.name;
                json_data.file_size = file.size;
                if(document.getElementById('criteria').classList.contains('selected')){
                    json_data.acc = document.getElementById('select_accredition').value;
                }
            } else{
                delete json_data.file_name;
                delete json_data.file_size;
            }

            if(bytes_read + chunk_size >= file.size){
                json_data.finished = 1;
            } else{
                delete json_data.finished;
            }   
    
            document.getElementById('file_upload_response').innerHTML = `
            <strong>Please Dont Close the Tab...</strong>
            `;
            socket.emit('recieve_file_data', json_data, (response)=>{
                response = JSON.parse(response);
                console.log(response);
                if(check_status_code(response)){
                    if(response.error){
                        console.log(response.error);
                        display_prog(response.error);
                        var button_ = document.getElementById('upload_file_button');
                        button_.disabled = false;
                        button_.classList.remove("unselected");
                    } else {
                        bytes_read += chunk_size;
                        var finished = json_data.finished ?? 0;
                        if(finished == 1){
                            display_prog("<div class='loader'></div><div>Processing the file</div>");
                        } else{
                            read_and_slice();
                        }
                    }
                }
            });
        }
    }  
    
    function read_and_slice(){
        if(file.size > bytes_read) {
            console.log("Reading next line info for the file ...");
            reader.readAsArrayBuffer(file.slice(bytes_read, bytes_read+(chunk_size)));
        } else {
            console.log("File Full read and sent ...");
        } 
    }

    read_and_slice();
}

socket.on("processed_file_data", (response)=>{
    file_resp = document.getElementById('file_upload_response');
    response = JSON.parse(response);
    flash_msg.innerHTML = '';

    error = response.error ?? 0;
    if(error){
        display_prog(error);
    } else{
        display_prog('File data has been Updated');
        file_resp.innerHTML = response.data; 
    }
    fileInput.value = "";
    var button_ = document.getElementById('upload_file_button');
    button_.disabled = false;
    button_.classList.remove("unselected");
});

function formatted_data_for_excel(data){
    var jsonData = [];
    var counter=1;
    var temp_dict = {};
    for(var x of data){
        temp_dict = {};
        temp_dict['Serial no'] = counter;
        temp_dict['Category'] = x['category'];
        temp_dict['Definition'] = x['definition'];
        jsonData.push(temp_dict);
        counter++;
    }
    return jsonData;
}

function download_category_data(folder = false){
        var jsonData = [];
        var file_name = "category_data"
        if(folder){
            console.log("Categories for folder");
            file_name = document.querySelector('.select_folder').value;
            jsonData = formatted_data_for_excel(folder_cat);
        } 
        else{
            console.log("All the Categories");
            jsonData = formatted_data_for_excel(available_cat);
        }
        const ws = XLSX.utils.json_to_sheet(jsonData);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');

        // Create a Blob
        // Generate Excel file content
        const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
        const blob_ = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

        // Create a download link
        const url = URL.createObjectURL(blob_);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${file_name}.xlsx`;

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
}

function add_criteria_excel(){

    flash_msg.innerHTML = '';
    var cat_options = document.getElementById('criteria_options');
    cat_options.style.display = 'flex';  
    cat_options.innerHTML = `
    <div class="flex column " style="gap:18px;">
        <div class="flex row gap-25" style="justify-content: space-between;">
            <div style="font-size: 19px; font-weight: 600;">
            Uptaing Criteria using Excel
            </div>
            <div class="flex align-center" onclick="remove_options_for_criteria()" style="cursor: pointer;">
                <img src="/static?file_name=x-regular-24.png" alt="" style="height: 25px;">
            </div>
        </div>

        <div id="instructions" class="flex column" style="gap:7.5px;">
            <div style=" font-weight: 500; font-size: 17px;">
                Please follow the instructions as given below : 
            </div>
            <ul style="gap:1px; margin-left: 5px; font-size: 16.5px;" class="flex column">
                <li>1. The file should be an <strong>Excel (.xlsx)</strong> file</li>
                <li>2. The file size limit is <strong>50MB</strong>.</li>
                <li>3. Please make sure to <strong>add the Categories</strong> prior to uploading the file.</li>
                <li>4. Check the format of your excel file before uploading : 
                    <ul style="padding-left: 20px; padding-top:3px;">
                        <li><strong>a. Serial no :</strong> Serial Numbering of the rows</li>
                        <li><strong>b. Criteria :</strong> The Criteria letter code
                            <em>(All available categories can be downloaded from above)</em></li>
                        <li><strong>c. Definition : </strong>Definition for the criteria <em>(Can be changed later)</em></li>
                        <li><strong>d. Category :</strong> Categories for which that particular criteria needs to be added to</li>
                        <li><em>(In case of more than one category for a particular category seperate the names using a comma , )</em></li>
                    </ul>  
                </li>
            </ul>
            <div class="flex row gap-10" style="justify-content: space-between; margin-top: 12px;">
                <form action='' methods='' enctype="multipart/form-data" for="fileInput" id="file_form">
                    <label for="fileInput" id="form_label">
                        <input type="file" id="fileInput" accept=".xlsx,.csv" name="files" style="border: none !important;"/>
                    </label>
                </form>
                <button id="upload_file_button" class="unselected" onclick="upload_excel()" style="padding: 5px 9px !important; font-size: 15px;" disabled>Upload File</button>
            </div>
        </div>
        
        <div id="file_upload_response" class="flex column gap-10"> 
        </div>

    </div>
    `;
    file_input = document.getElementById("fileInput");
    file_input.addEventListener("change", enable_button);
}

function formatted_data_for_excel_criteria(){
    var jsonData = [];
    var counter=1;
    var temp_dict = {};
    for(var x of criteria){
        temp_dict = {};
        temp_dict['Serial no'] = counter;
        temp_dict['Criteria'] = x['criteria'];
        temp_dict['Definition'] = x['definition'];
        temp_dict['category'] = "";
        for(var _ of x['category']){
            temp_dict['category'] += _ + ','
        }

        jsonData.push(temp_dict);
        counter++;
    }
    return jsonData;
}

function download_criteria_data(){
    var jsonData = [];
        var file_name = "criteria_data"
        jsonData = formatted_data_for_excel_criteria();

        const ws = XLSX.utils.json_to_sheet(jsonData);
        const wb = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(wb, ws, 'Sheet1');

        // Create a Blob
        // Generate Excel file content
        const excelBuffer = XLSX.write(wb, { bookType: 'xlsx', type: 'array' });
        const blob_ = new Blob([excelBuffer], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });

        // Create a download link
        const url = URL.createObjectURL(blob_);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${file_name}.xlsx`;

        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
}
