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
async def cryptocurrencies(user_name:str, password:str, crypo_name:str, crypo_short_name:str):
    if db.find_user(user_name, password)['id'] == 0:
        return {'status': 'fail',
                'reason': 'invalid account'}
    db.add_crypto(crypo_name, crypo_short_name, True)
    return {'status': 'ok'}
