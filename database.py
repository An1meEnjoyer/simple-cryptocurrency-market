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
       
       
    def sell(self, user_id:int, first_crupto_id:int, second_crupto_id:int, price:float, value:float) -> None:
        # get aviable crypto balance
        self.cursor.execute("SELECT value FROM balance WHERE user_id = %s AND crypto_id = %s;", (user_id, first_crupto_id))
        first_crypto_balance_before = self.cursor.fetchone()[0]
        
        if first_crypto_balance_before >= value:
            first_crypto_balance_after = first_crypto_balance_before - value
            
            self.cursor.execute("SELECT value FROM balance WHERE user_id = %s AND crypto_id = %s;", (user_id, second_crupto_id))
            second_crypto_balance_before = self.cursor.fetchone()
            
            second_crypto_balance_after = value*price
            if second_crypto_balance_before:
                second_crypto_balance_after += second_crypto_balance_before[0]
            else:
                self.cursor.execute("INSERT INTO balance (user_id, crypto_id, value) VALUES (%s, %s, 0);", (user_id, second_crupto_id))
            
            self.cursor.execute(""" UPDATE balance
                                    SET value = %s
                                    WHERE user_id = %s AND crypto_id = %s;""",
                                    (first_crypto_balance_after, user_id, first_crupto_id))
            
            self.cursor.execute(""" UPDATE balance
                                    SET value = %s
                                    WHERE user_id = %s AND crypto_id = %s;""",
                                    (second_crypto_balance_after, user_id, second_crupto_id))
            
            self.save_changes()
            
       
    def buy(self, user_id:int, first_crupto_id:int, second_crupto_id:int, price:float, value:float) -> None:
        # get aviable crypto balance
        self.cursor.execute("SELECT value FROM balance WHERE user_id = %s AND crypto_id = %s;", (user_id, second_crupto_id))
        second_crypto_balance_before = self.cursor.fetchone()[0]
        
        if second_crypto_balance_before >= value*price:
            second_crypto_balance_after = second_crypto_balance_before - value*price
            
            self.cursor.execute("SELECT value FROM balance WHERE user_id = %s AND crypto_id = %s;", (user_id, first_crupto_id))
            first_crypto_balance_before = self.cursor.fetchone()
            
            first_crypto_balance_after = value
            if first_crypto_balance_before:
                first_crypto_balance_after += first_crypto_balance_before[0]
            else:
                self.cursor.execute("INSERT INTO balance (user_id, crypto_id, value) VALUES (%s, %s, 0);", (user_id, first_crupto_id))
            
            self.cursor.execute(""" UPDATE balance
                                    SET value = %s
                                    WHERE user_id = %s AND crypto_id = %s;""",
                                    (first_crypto_balance_after, user_id, first_crupto_id))
            
            self.cursor.execute(""" UPDATE balance
                                    SET value = %s
                                    WHERE user_id = %s AND crypto_id = %s;""",
                                    (second_crypto_balance_after, user_id, second_crupto_id))
            
            self.save_changes()
            
            
    def save_changes(self) -> None:
        self.conn.commit()
        
        
    def get_data(self, table:str) -> list:
        self.cursor.execute("SELECT * FROM %s;" % table)
        return self.cursor.fetchall()
    
    
    def __dell__(self) -> None:
        # close db connection
        self.cursor.close()
        self.conn.close()
    