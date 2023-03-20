import psycopg2

from SETTINGS import POSTGRESS_SETTINGS


class Connect():
    def __init__(self, settings = POSTGRESS_SETTINGS) -> None:
        # connect to db
        self.conn = psycopg2.connect(**settings)
        self.cursor = self.conn.cursor()
       
    
    # - - - - - - - - - - - - - - - - - - GENERAL FUNCS - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_data(self, table:str) -> list:
        # select all lines from table
        self.cursor.execute("SELECT * FROM %s;" % table)
        return self.cursor.fetchall()
    
    
    def save_changes(self) -> None:
        # just commit
        self.conn.commit()
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    
    # - - - - - - - - - - - - - - - - - - USERS FUNCS - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def find_user(self, user_name:str, password:str) -> dict:
        self.cursor.execute("SELECT id, superuser FROM users WHERE username = %s AND password = %s;", (user_name, password))
        sup = self.cursor.fetchone()
        
        if not sup:
            return {'id': 0, 'superuser': 0}
        return {'id': sup[0], 'superuser': sup[1]}
    
    
    def add_user(self, username:str, password:str) -> None:
        # register
        self.cursor.execute("INSERT INTO users (username, password) VALUES(%s, %s);", (username, password))
        self.save_changes()
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    
    # - - - - - - - - - - - - - - - - - - CRYPTO  FUNCS - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def add_crypto(self, user_name:str, password:str, crypto_name:str, short_name:str) -> None:
        # add new cryptocurrency (only for superuser)
        if self.find_user(user_name, password)['superuser']:
            self.cursor.execute("INSERT INTO cryptocurrencies (name, short_name) VALUES (%s, %s);", (crypto_name, short_name))
            self.save_changes()
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
       
    # - - - - - - - - - - - - - - - - - - BALANCE FUNCS - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_bal(self, user_name:str, password:str) -> dict:
        user_id =  self.find_user(user_name, password)['id']
        if not user_id:
            return {}
        self.cursor.execute("SELECT crypto_id, value FROM balance WHERE user_id = %s" % (user_id))
        
        pretty_bal = {}
        for i in self.cursor.fetchall():
            pretty_bal[i[0].strip()] = float(i[1])
            
        return pretty_bal
    

    def set_bal(self, user_name:str, password:str, crypto_id:str = 'USDT', value:float = 100) -> None:
        # add balance
        user = self.find_user(user_name, password)
        if not user:
            return None
        self.cursor.execute("INSERT INTO balance (user_id, crypto_id, value) VALUES (%s, %s, %s);", (user['id'], crypto_id, value))
        self.save_changes()
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        
        
    # - - - - - - - - - - - - - - - - - - SELL/BUY  FUNCS - - - - - - - - - - - - - - - - - - - - - - - - - -
    def sell(self, user_id:int, first_crupto_id:int, second_crupto_id:int, price:float, value:float) -> None:
        # sell first_crupto to second_crupto
        
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
        # buy first_crupto by second_crupto
        
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
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    
    def __dell__(self) -> None:
        # close db connection
        self.cursor.close()
        self.conn.close()
    