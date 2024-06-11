import sqlite3
from time import sleep, time
from threading import Thread


class database:

    def __init__(self):
        self.connections = {} 
        self.dict_connection = None       

    def connection_is_alive(self, connection):
        try:
            while True:
                start_time = self.connections.get(connection)

                if start_time is not None:
                    now_time = time()
                    if now_time - start_time >= 60:
                        self.connections.pop(connection)
                        connection.close()
                        return
                    sleep(60 - (now_time - start_time)+ 1)
                else:
                    sleep(1)
        except Exception as e:
            print("Exception in Thread of connection", e)
            self.connections.pop(connection)
            connection.close()

    def get_connection(self):
        while True:
            try:
                if self.connections:
                    con = list(self.connections.keys())
                    connection = con.pop()
                    self.connections.pop(connection)
                    return connection
                else:
                    connection = sqlite3.connect('database.db', check_same_thread=False, isolation_level=None)
                    Thread(target = self.connection_is_alive, args=(connection,)).start()
                    return connection
            except Exception as e:
                print("Connection Error : ", e)
                sleep(1)

    def execute_query(self, query):
        connection = self.get_connection()
        cursor = connection.cursor()

        try:
            cursor.execute(query)
            data = cursor.fetchall()
        
        except Exception as e:
            data = 'failed'
            print("Exception while executing", e)

        self.connections[connection] = time()
        return data

    def dict_query(self,query):
        
        def dict_factory(cursor, row):
            fields = [column[0] for column in cursor.description]
            return {key: value for key, value in zip(fields, row)}

        connect = self.dict_connection
        if not connect:
            connect = sqlite3.connect('database.db')
            connect.row_factory = dict_factory
        cursor = connect.cursor()

        try:
            cursor.execute(query)
            data = cursor.fetchall()
        except Exception as e:
            data = None
            print("Exception while dict return executing :", e)

        self.dict_connection = connect
        return data


    def credentials(self):
        connection = sqlite3.connect('database.db', check_same_thread=False)

        data = connection.execute('select * from creds')
        data = data.fetchall()
        connection.close()
        return data[0][0]

connection = database()