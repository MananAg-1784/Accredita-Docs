# Accredita-Docs
This web application focuses on efficient document classification and retrieval through a user-friendly interface for college departments. It seamlessly integrates with existing storage solutions by using Google Drive API, ensuring data security and reliability.

## Table of Content

1. [Features](#features)
2. [Modules and Working](#modules-and-working)
    * [User Management](#user-management)
    * [Document Classification and Storage](#document-classification-and-storage)
    * [File Management](#file-management)
    * [Administrative Update](#administrative-updates)
3. [Database Structure](#database-structure)
4. [Installation](#installation)
5. [Usage](#usage)
6. [License](#license)
7. [Contact](#contact)


## Features
* **User management** : Manage department teachers and access to various roles
* **Administrative updates** : Updating and managing users, files, folders, etc.
* **Document Classification and Storage** : Stores and classifies files in an organised manner that specify files content
* **File Management** : Upload and track activities of all files
* **Serach and Retrieval** : Filters and classifies files based on criteria's 

## Modules and Working

### User Management 
Each user is associated with a department under which they perform all tasks. Users are assigned one of the following four roles :

* **Owner** : Utilizes its Google Drive spcae for the Department files. (Same level as the admin)
* **Admin** : Manages the department, control access, oversees folders and files, etc.
* **Editor**  : Upload, Update, and view files.
* **Viewer** : View and Classify files.

| Permission                                                   | Owner | Admin | Editor | Viewer |
|--------------------------------------------------------------|:-----:|:-----:|:------:|:------:|
| Managers folders within the department                       |   ✓   |   ✓   |        |        |
| Controls access for other teachers                           |   ✓   |   ✓   |        |        |
| Updates criterias and classification codes                   |   ✓   |   ✓   |        |        |
| Uploads and Update files                                     |   ✓   |   ✓   |   ✓    |        |
| Track activity of all files                                  |   ✓   |   ✓   |   ✓    |        |
| Views and Classify files                                     |   ✓   |   ✓   |   ✓    |   ✓    |

### Document Classification and Storage

- Each file is assciated with `Classification Codes (4-5 letters)` that specify the file's content (eg. SYLR, ALCO)
- Files can be uploaded to oonly those folders added by the admin in the department
- Folders can be associated with classification codes that specify the type of files inside the folder
- Creates criteria associated with classification codes, which are created under specific accreditations (e.g., NAAC, NBA).

### File Management

- Filters and classifies files based on folder, criteria, classification code, etc.
- Uploads multiple files to Google Drive in a specific format.
- Tracks activities for the last 7 days.
- Update, Remane, Move and Trash Files
- File Format :
  `yyyymmdd_ClassificationCode_name.extension`
  <br>In case of files associated with multiple classification code seperate the code using a comma (,)
  <br>Example : `20240612_SYLR_Syllabus for Students.doc` `20240612_SYLR,LRNG_Syllabus for Students.doc`

### Administrative Updates

- Update, create and modify list of folders, categories and criterias
- Manage access roles to the users of the department
- Keep track of all the activity of files

## Database Structure

![Database Schema Diagram](/database_schema.png)

## Installation

1. Clone the repository:

    ```bash
    https://github.com/MananAg-1784/Accredita-Docs.git
    ```

2. Install the required dependencies using pip and the provided requirements file:

    ```bash
    pip install -r requirements.txt
    or
    pip3 install -r requirements.txt
    ```

    This command will install all the necessary Python packages specified in the `requirements.txt` file.

3. Change the Api Secret Key in the `config.py` file

   ```bash
   api_secret = 'Accredita-Doc'
   ```

5. Update the required data in the `setup.json` file :

    ```bash
    {
        "timezone":"Asia/Kolkata",
        "domain":"gamil.com",
        "auth_redirect":"http://localhost:5000/callback",
        "admin_email" : "Aministrator email for the app",
        "cloud_email": "Email used to create the OAuth Creds",
        "creds": 
        {
            "web" : "The credentials data from Google Cloud OAuth 2.0 Client IDs"
        }
    }
    ```

    To get the credentials for OAuth (Login using gmail) follow the following steps:
      - Go to google Cloud Services and Create a new Project
      - Enable : **Drive API**, **Peoples API**, **Drive Activity API**
      - Create a OAuth Client ID :
           <br> Application Type : `Web Application`
           <br> Add Authorized redirect URIs (NOTE: include `/callback` uri)

6. Run the `setup.py` to update the data into the database.

    `python -m setup`

   ```bash
    1. Update data from setup.json
    2. Clear the database
    Choose the option :
   ```

## Usage

To execute the program in `localhost`, add these two lines in the `run.py` file :

```bash
# After initialising the app
app.config["DEBUG"] = True
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"
```

To change the port of the server, replace the port in WSGIerver in `run.py`

```bash
WSGIServer(('0.0.0.0', _port_ ), app, log=None).serve_forever()
```

Open the terminal in the same directory as the `run.py`

```bash
python -m run   # In Windows
or
gunicorn -k gevent -w 1 run:app   # In Ubuntu
```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Contact 

For any questions or feedback, please contact at `mananagarwal1784@gmail.com` <br>
Visit my [Website](https://manan-portfolio.ddns.net/) to check out my works



