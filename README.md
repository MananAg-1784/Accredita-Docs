# Accredita-Docs
This web application focuses on efficient document classification and retrieval through a user-friendly interface for college departments. It seamlessly integrates with existing storage solutions by using Google Drive API, ensuring data security and reliability.

## Table of Content

1. [Features](#features)
2. [Modules and Working](#modules-and-working)
    - [User Management](#user-management)
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

### Classification Structure

### File Management

### Administrative Updates

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

3. Update the required data in the database using the setup files
   
5. Change the Api Secret Key

## Usage

## License

## Contact 

Open the terminal in the same directory as the run.py

```bash
python -m run
```
