socket = io("/upload", {autoConnect:false});
socket.on('connect', function(){
    console.log("Socket Connected...");
});
socket.on('disconnect', function(){
    console.log("Socket disconnected...");
    filesToBeUploaded = 0;
    flash_msg.innerHTML = '';
    var x = document.getElementsByClassName('uploading_file_data');
    for(var i of x){
        var class_ = i.querySelector('#progress_display').classList;
        item_no = i.id.replace('uploading_','');
        if(class_.contains('transfer')){
            update_uploading_progress(item_no, percent = null, progress = null, error = 'Disconnected');
        } else if(class_.contains('uploaded')){
            console.log("file uploaded..");
        } else{
            update_uploading_progress(item_no, percent = null, progress = null, error = 'File will be uploaded from server');
        }
    }
    alert('Disconnected... Please Connect to internet and try again');
});

var uploading_files = [];
var upload_lock = 0;
var retry_upload = {};
var filesToBeUploaded = 0;

function upload_file_data(){
    // check if the function is working or not
    if( upload_lock){
        console.log("Function already running..")
        return
    } else{
        console.log("Function running ... upload_file_data()")
        upload_lock = 1;
    }

    filesToBeUploaded = uploading_files.length;
    console.log('Total files to be uploaded : ',filesToBeUploaded );
    if(!socket.connected){
        socket.connect();
    }
    socket.emit('clear_cache', 1,(resp)=>{
        while(filesToBeUploaded > 0){
            resp = upload_file(uploading_files[0]);
            console.log(resp);
            if(resp.error){
                console.log("Error in transfering file...");
                update_uploading_progress(uploading_files[0].itemNo,percent = null, progress=null, error = resp.error)
                delete files_uploaded[uploading_files[0].itemNo];
            } else{
                console.log("All data transfered for the file...");
            }
            // after the file data is completely transfered
            uploading_files.shift();
            filesToBeUploaded = uploading_files.length;
            console.log('total files to be uploaded : ',filesToBeUploaded );
        }
        upload_lock = 0;
        console.log("Lock Lifted...");
    });
}

function retry_upload_file(item_no){
    flag = 0;
    item_no_list = [];
    console.log(item_no);
    console.log(retry_upload[item_no]);
    for(var x in files_list){
        console.log(files_list[x]);
        if(retry_upload[item_no].name === files_list[x].name && retry_upload[item_no].size === files_list[x].size && retry_upload[item_no].type === files_list[x].type){
            delete retry_upload[item_no];
            item_no_list.push(parseInt(item_no));
            item_no = x;
            console.log('deleted : ', item_no);
            flag = 1;
        }
    }
    if(flag == 0){
        files_list[item_no] = retry_upload[item_no];
        display_file_data(item_no);
    }
    for(var x in retry_upload){
        console.log(retry_upload[x]);
        if(retry_upload[x].name === files_list[item_no].name && retry_upload[x].size === files_list[item_no].size && retry_upload[x].type === files_list[item_no].type){
            delete retry_upload[x];
            console.log('deleted : ', item_no);
            item_no_list.push(parseInt(x));
        }
    }
    console.log(item_no_list);
    up_files = document.querySelectorAll('.uploading_file_data');
    for(var x of up_files){
        id_ = x.id.replace('uploading_', '');
        id_ = parseInt(id_);
        if(item_no_list.includes(id_)){
            console.log("Removing from files_upload...", x);
            document.getElementById('uploading_data').removeChild(x);
        }
    }
    
}
 
function update_uploading_progress(item_no, percent = null, progress = null, error = null){
    var progress_ = document.querySelector(`#uploading_${item_no} #progress`);
    console.log(progress_);
    console.log(percent, progress, error);
    if(percent!= null){
        progress_.querySelector('#already_uploaded').style.width = `${percent.percent}%`
        progress_.querySelector('#pending_upload').style.width = `${100 - percent.percent}%`;
        progress_.querySelector('#progress_percent').innerHTML = `${percent.size}`;

    } else if(progress != null){
        if(progress === 'upload'){
            progress_.querySelector('#display_progresses').innerHTML = 'Uploading in Drive';
        } else if(progress === 'uploaded'){
            progress_.querySelector('#progress_display').classList.add('uploaded');
            progress_.querySelector('#progress_display').innerHTML = '👍 File Uploaded';
        } else {
            progress_.querySelector('#progress_display').classList.add('uploaded');
            progress_.querySelector('#progress_display').innerHTML = `File uploaded only in ${progress}`;
        }

    } else if(error != null){
        html_data = `   
        <div class="flex row" style="align-items:center; justify-content: space-between; width: 100%;">
            <div style="max-width:250px; font-weight: 600; color: #ff0000ed; font-size: 15.5px;" class="cut-text">
                <abbr title="${error}">${error}</abbr>
            </div>
            <div id="retry" onclick = "retry_upload_file(${item_no})">
                Retry
            </div>
        </div>
        `;
        progress_.querySelector('#progress_display').classList.add('transfer');
        progress_.querySelector('#progress_display').innerHTML = html_data;
        progress_.querySelector('#already_uploaded').style.backgroundColor = '#ff0000ed';
        retry_upload[item_no] = files_uploaded[item_no].data;
    }

}


function upload_file(file){
    // file-data => itemNo, name, size, mimeType, categories, folders, data==> file data
    console.log("Uploading file ...", file.name);
    console.log("Total size : ", file.size);
    
    var bytes_read = 0;
    var chunk_size = 1024*100;
    var reader = new FileReader();
    if(file.size > 200*1024*1024){
        return {error: "File size to big"};
    }
    
    var transfer_data = {itemNo: file.itemNo, name:file.name, size:file.size, mimeType:file.mimeType , categories:file.categories , folders:file.folders , segment:0 , data:'', new_file_upload: 1 };
    console.log(transfer_data);
    
    reader.onload = function (e) {
        if (reader.error) {
            return {error: "Error in reading the file"};
        }
        
        if(reader.readyState != reader.LOADING){
            data = reader.result;
            transfer_data.data = new Uint8Array(data);
            transfer_data.segment += 1;
            
            if(bytes_read != 0){
                delete transfer_data.folders;
                delete transfer_data.categories;
                delete transfer_data.new_file_upload;
            }
            if(bytes_read + chunk_size >= file.size){
                transfer_data.finished = 1;
            } else{
                delete transfer_data.finished;
            }   

            console.log(transfer_data);
            var percent = 0;
            socket.emit('send_file_data', transfer_data, (response)=>{
                response = JSON.parse(response);
                console.log(response);
                if(check_status_code(response)){
                    if(response.error){
                        console.log("Error in file transfer...");
                        update_uploading_progress(file.itemNo,percent = null, progress=null, error = response.error)
                        delete files_uploaded[file.itemNo];
                        return;
                    } else {
                        bytes_read += chunk_size;
                        if(bytes_read >= file.size){
                            percent = 100;
                            bytes_read = file.size;
                            document.querySelector(`#uploading_${file.itemNo} #progress_display`).classList.remove('transfer');
                            console.log('Finished file uploading all the data : ', response.response);
                        } else{
                            percent = Math.round((bytes_read / file.size)*100);
                        }
                        update_uploading_progress(file.itemNo, {percent:percent,
                        size:formatFileSize(bytes_read)});
                        read_and_slice();
                    }
                }
            });
        }
    }  

    function read_and_slice(){
        if(file.size > bytes_read) {
            console.log("Reading next line info for the file ...");
            reader.readAsArrayBuffer(file.data.slice(bytes_read, bytes_read+(chunk_size)));
        } else {
            console.log("File Full read and sent ...");
        } 
    }
    read_and_slice();
    return {error : null};
}

socket.on('progress_report', function(data){
    console.log('Recieved progress log...',data);
    data = JSON.parse(data);
    if(data.progress){
        update_uploading_progress(data.itemNo, percent = null,progress = data.progress);
    }
    else if(data.error){
        update_uploading_progress(data.itemNo,percent = null, progress =null,  error = data.error);
    }
});

socket.on('activity_updated', function(data){
    console.log('Recieved progress log...',data);
    data = JSON.parse(data);
    if(data.data === 1){
        // Loading for updates 
        flash_msg.innerHTML = '<div class="loader"></div><div>Looking for any updates...</div>';
        console.log(flash_msg);
    } else if(data.data === 2){
        flash_msg.innerHTML = '';
    } else{
        flash_msg.innerHTML = data.data;
    }
});

