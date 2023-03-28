# ---------------------------------------------------------------------------------------------
# there main api that works with db
# ------------------------------------------
# db is postgresql that have this structure:
# 
# - - - - - - - - - - - - users - - - - - - - - - - - - - - - - -
# username  | character varying(30) | not null | PRIMARY KEY
# password  | character varying(30) | not null |
# superuser | boolean |
# 
# - - - - - - - - - - - - cryptocurrencies - - - - - - - - - - - -
# name       | character varying(1000) | not null |
# short_name | character varying(100)  | not null | PRIMARY KEY
# 
# - - - - - - - - - - - - balance - - - - - - - - - - - - - - - -
# id        | integer        | not null | PRIMARY KEY
# user_id   | character(30)  | not null | FOREIGN KEY -> users(username)
# crypto_id | character(100) | not null | FOREIGN KEY -> cryptocurrencies(short_name)
# value     | numeric
# ---------------------------------------------------------------------------------------------
import psycopg2
import requests

from SETTINGS import POSTGRESS_SETTINGS, CRYPTO_API_URL


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
        # trying to find user in db
        # returns error if something wrong
        try:
            self.cursor.execute("SELECT superuser FROM users WHERE username = %s AND password = %s;", (user_name, password))
            user = self.cursor.fetchone()
        except:
            return {'status': 'error', 'id': 0, 'superuser': 0}

        if not user:
            return {'status': 'error', 'id': 0, 'superuser': 0}
        return {'status': 'ok', 'id': user_name, 'superuser': user[0]}
    
    
    def add_user(self, username:str, password:str) -> None:
        # register (add accaunt to db)
        try:
            self.cursor.execute("INSERT INTO users (username, password) VALUES(%s, %s);", (username, password))
            self.save_changes()
        except:
            return {'status': 'error'}
        return {'status': 'ok'}
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    
    # - - - - - - - - - - - - - - - - - - CRYPTO  FUNCS - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def add_crypto(self, user_name:str, password:str, crypto_name:str, short_name:str) -> dict:
        # add new cryptocurrency (only for superuser)
        if not self.find_user(user_name, password)['superuser']:
            return {'status': 'invalid account'}
        
        self.cursor.execute("INSERT INTO cryptocurrencies (name, short_name) VALUES (%s, %s);", (crypto_name, short_name))
        self.save_changes()
        return {'status': 'ok'}
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
       
    # - - - - - - - - - - - - - - - - - - BALANCE FUNCS - - - - - - - - - - - - - - - - - - - - - - - - - - -
    def get_bal(self, user_name:str, password:str) -> dict:
        # returns dict with all coins on accaunt
        # like {'BTC': 3, 'ETH': 0.5}
        user = self.find_user(user_name, password)
        if not user['id']:
            return {'status': 'invalid account'}
        self.cursor.execute("SELECT crypto_id, value FROM balance WHERE user_id = '%s'" % user['id'])
        
        pretty_bal = {'status': 'ok'}
        for i in self.cursor.fetchall():
            pretty_bal[i[0].strip()] = float(i[1])
            
        return pretty_bal
    
    
    def create_bal(self, user_name:str, password:str, crypto_id:str, balance:float) -> dict:
        # creating coin balance in db to user
        user = self.find_user(user_name, password)
        if not user:
            return {'status': 'invalid account'}
        
        try:
            self.cursor.execute("INSERT INTO balance (user_id, crypto_id, value) VALUES (%s, %s, %s);",
                                (user['id'], crypto_id, balance))
        except Exception as e:
            return {'status': str(e)}
        self.save_changes()
        return {'status': 'ok'}
        
        
    def update_bal(self, user_name:str, password:str, crypto_id:str, balance:float) -> dict:
        # changes value in balance
        user = self.find_user(user_name, password)
        if not user:
            return {'status': 'invalid account'}
        
        try:
            self.cursor.execute(""" UPDATE balance SET value = %s
                                    WHERE user_id = %s AND crypto_id = %s;""",
                                    (balance, user['id'], crypto_id))
        except Exception as e:
            return {'status': str(e)}
        
        self.save_changes()
        return {'status': 'ok'}


    def set_bal(self, user_name:str, password:str, crypto_id:str = 'USDT', balance:float = 100) -> dict:
        # set balance or creating if it wasn't exists before
        user = self.find_user(user_name, password)
        if not user:
            return {'status': 'invalid account'}
        
        if crypto_id not in self.get_bal(user_name, password):
            self.create_bal(user_name, password, crypto_id, balance)
        else:
            self.update_bal(user_name, password, crypto_id, balance)
            
        self.save_changes()
        return {'status': 'ok'}


    def reload_bal(self, user_name:str, password:str):
        # set bal to only 100$ (deleting all coins and set USDT to 100)
        user = self.find_user(user_name, password)
        if not user:
            return {'status': 'invalid account'}
        
        balance = self.get_bal(user_name, password)
        
        for crypto in balance:
            self.update_bal(user_name, password, crypto, 0)
        self.set_bal(user_name, password, 'USDT', 100)
        return {'status': 'ok'}
        
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
        
        
    # - - - - - - - - - - - - - - - - - - SELL/BUY  FUNCS - - - - - - - - - - - - - - - - - - - - - - - - - -
    def sell(self, user_name:str, password:str, first_crypto:str, second_crypto:str, value:float) -> dict:
        # sell first_crypto to second_crypto
        
        user = self.find_user(user_name, password)
        if not user:
            return {'status': 'invalid account'}
        
        bal = self.get_bal(user_name, password)
        
        # gets first crypto balance
        # if not exists u cannot sell
        if first_crypto not in bal:
            return {'status': 'not enough coins'}
        first_balance = bal[first_crypto]
        
        # gets second crypto balance
        if second_crypto in bal:
            second_balance = bal[second_crypto]
        else:
            second_balance = 0
            self.create_bal(user_name, password, second_crypto, second_balance)
            
        price = get_price(first_crypto, second_crypto)
        if not price:
            return {'status': 'wrong pair'}
        
        will_get_second = price * value
        # changes balance
        first_balance -= value
        if second_balance < 0:
            return {'status': 'not enough coins'}
        
        second_balance += will_get_second
        
        # saves
        answer = self.update_bal(user_name, password, second_crypto, second_balance)
        if answer['status'] != 'ok':
            return answer['status']
        
        answer = self.update_bal(user_name, password, first_crypto, first_balance)
        if answer['status'] != 'ok':
            return answer['status']
        
        return {'status': 'ok'}
        

    def buy(self, user_name:str, password:str, first_crypto:str, second_crypto:str, value:float) -> None:
        # buy first_crypto by second_crypto
        
        user = self.find_user(user_name, password)
        if not user:
            return {'status': 'invalid account'}
        
        bal = self.get_bal(user_name, password)
        
        # gets second crypto balance
        # if not exists u cannot buy
        if second_crypto not in bal:
            return {'status': 'not enough coins'}
        second_balance = bal[second_crypto]
        
        # gets first crypto balance
        if first_crypto in bal:
            first_balance = bal[first_crypto]
        else:
            first_balance = 0
            self.create_bal(user_name, password, first_crypto, first_balance)
            
        price = get_price(first_crypto, second_crypto)
        if not price:
            return {'status': 'wrong pair'}
        
        need_second = price * value
        # changes balance
        second_balance -= need_second
        if second_balance < 0:
            return {'status': 'not enough coins'}
        
        first_balance += value
        
        # saves
        answer = self.update_bal(user_name, password, first_crypto, first_balance)
        if answer['status'] != 'ok':
            return answer['status']
        
        answer = self.update_bal(user_name, password, second_crypto, second_balance)
        if answer['status'] != 'ok':
            return answer['status']
        
        return {'status': 'ok'}
    # - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    
    
    def __dell__(self) -> None:
        # close db connection
        self.cursor.close()
        self.conn.close()
    
    
def get_price(first_crypto:str, second_crypto:str):
    # returns price of pair using third party api
    
    url = CRYPTO_API_URL + first_crypto + second_crypto
  
    data = requests.get(url)
    data = data.json()
    
    try:
        return float(data['price'])
    except:
        return None