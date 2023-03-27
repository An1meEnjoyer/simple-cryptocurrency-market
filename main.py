from fastapi import FastAPI
from api import Connect

app = FastAPI()
db = Connect()


@app.get('/')
async def root():
    return {'message': 'ok'}


@app.get('/cryptocurrencies')
async def cryptocurrencies():
    return db.get_data('cryptocurrencies')


@app.get('/add_crypto')
async def add_crypto(user_name:str, password:str, crypo_name:str, crypo_short_name:str):
    return db.add_crypto(user_name, password, crypo_name, crypo_short_name)


@app.get('/balance')
async def balance(user_name:str, password:str):
    return db.get_bal(user_name, password)


@app.get('/set_balance')
async def set_balance(user_name:str, password:str):
    return db.set_bal(user_name, password)


@app.get('/buy')
async def buy(user_name:str, password:str, first_crypto:str, second_crypto:str, value:float):
    return db.buy(user_name, password, first_crypto, second_crypto, value)
    
    
@app.get('/sell')
async def sell(user_name:str, password:str, first_crypto:str, second_crypto:str, value:float):
    return db.sell(user_name, password, first_crypto, second_crypto, value)
    
