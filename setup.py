import sqlite3
from json import loads, dumps

# Creating connection to the database
connection = sqlite3.connect('database.db', check_same_thread=False, isolation_level=None)

if __name__ == '__main__':
    
    print("1. Update data from setup.json")
    print("2. Clear the database")
    choice = int(input("Choose the option : "))

    if choice == 1:
        # Reading the data from the setup.json file
        with open('setup.json') as f:
            data = loads(f.read())

        # updating the creds
        connection.execute('delete from creds')
        connection.execute(f"insert into creds values('{dumps(data['creds'])}') ")
        # deleting all the users - login again to get new token for the creds
        connection.execute('delete from user') 
        connection.execute('update department set owner = "" ')

        # udating the other values
        connection.execute('drop table if exists setup;')
        connection.execute('create table setup(timezone text, domain text, auth_redirect text, admin_email text)')
        connection.execute(f"insert into setup values('{data['timezone']}','{data['domain']}','{data    ['auth_redirect']}','{data['admin_email']}')")
    
    elif choice == 2:
        cursor = connection.cursor()
        tables = cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        for table in tables.fetchall():
            cursor.execute(f'delete from {table[0]}')
        
        connection.commit()
        cursor.close()


