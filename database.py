import psycopg2

from SETTINGS import POSTGRESS_SETTINGS


class Connect():
    def __init__(self, settings = POSTGRESS_SETTINGS) -> None:
        # connect to db
        self.conn = psycopg2.connect(**settings)
        self.cursor = self.conn.cursor()


    def add_crypto(self, name:str, short_name:str, superuser:bool = False) -> None:
        if superuser:
            self.cursor.execute("INSERT INTO cryptocurrencies (name, short_name) VALUES(%s, %s);", (name, short_name))
    
    
    def add_user(self, username:str, password:str) -> None:
        self.cursor.execute("INSERT INTO users (username, password) VALUES(%s, %s);", (username, password))
            
            
    def save_changes(self) -> None:
        self.conn.commit()
        
        
    def get_data(self, table:str) -> list:
        self.cursor.execute("SELECT * FROM %s;" % table)
        return self.cursor.fetchall()
    
    
    def __dell__(self) -> None:
        # close db connection
        self.cursor.close()
        self.conn.close()
    