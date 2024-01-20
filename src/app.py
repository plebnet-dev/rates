from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
import starlette.status as status

from locale import atof, setlocale, LC_NUMERIC
import logging
import requests
import coinbasepro as cbp

def get_block_height():
    url = "https://api.blockchair.com/bitcoin/stats"
    res = requests.get(url)
    data = res.json()
    height = data['data']['best_block_height']
    return height


def coindesk_btc_fiat(symbol):
    # batch the requests together via asyncio or multiprocessing
    setlocale(LC_NUMERIC, '')
    url = f'https://api.coindesk.com/v1/bpi/currentprice/{symbol}.json'
    response = requests.get(url)
    ticker = response.json()
    time = ticker["time"]['updated']
    rate = ticker['bpi'][symbol]['rate']

    parsed_rate = atof(rate.replace(',', ''))

    return time, parsed_rate

def coinbase_btc_fiat(symbol):
    
    client = cbp.PublicClient()

    result = client.get_product_ticker(f'BTC-{symbol}')
    rate = float(result['price'])
    dt = result['time']
    time = dt.strftime("%b %d, %Y %H:%M:%S UTC")
    return time, rate

title = "sats converter"
description = "simple web app to convert fiat to btc"

app = FastAPI(
    title=title,
    description=description,
    version="0.0.1 alpha",
    contact={
        "name": "bitkarrot",
        "url": "http://github.com/bitkarrot",
    },
    license_info={
        "name": "MIT License",
        "url": "https://mit-license.org/",
    },
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5000",
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="static"), name='static')
templates = Jinja2Templates(directory='templates/')

fiatlist = ['USD', 'EUR', 'JPY', 'CAD', 'AUD', 'GBP', 'PLN']

# initial get for index page
@app.get("/")
async def initial_page(request: Request):

    satsamt = 100000000
    currency = 'USD'
    # time, rate = coindesk_btc_fiat(currency)
    time, rate = coinbase_btc_fiat(currency)
    btcusd = "%.2f" % (rate)
    moscowtime = int(100000000/float(btcusd))
    height = get_block_height()
    btcusd = "{:,}".format(float(btcusd)) #formatting with commas

    return templates.TemplateResponse("index.html",
                                      context={
                                          'request': request,
                                          'title': "Sats Converter",
                                          'fiat': btcusd,
                                          'fiattype': currency,
                                          'fiatlist': fiatlist,
                                          'satsamt': satsamt,
                                          'moscow': moscowtime,
                                          'blockheight': height,
                                          'lastupdated': time})

@app.get("/btc")
async def redirectpage(request: Request):
    return RedirectResponse('/', status_code=status.HTTP_302_FOUND)


# for btc page
@app.post("/btc")
async def submit_form(request: Request, selected: str = Form(...)):     # trunk-ignore(ruff/B008)
    try:
        if selected is None:
            return RedirectResponse('/', status_code=status.HTTP_302_FOUND)

        # time, rate = coindesk_btc_fiat(selected)
        time, rate = coinbase_btc_fiat(currency)

        btcfiat = "%.2f" % rate
        moscowtime = int(100000000/float(btcfiat))
        height = get_block_height()
        btcfiat = "{:,}".format(float(btcfiat))  #formatting with commas
        satsamt = 100000000


        return templates.TemplateResponse("index.html",
                                          context={
                                              'request': request,
                                              'fiattype': selected,
                                              'fiat': btcfiat,
                                              'fiatlist': fiatlist,
                                              'satsamt': satsamt,
                                              'moscow': moscowtime,
                                              'blockheight': height,
                                              'lastupdated': time,
                                              'title': "Sats Converter"})
    except Exception as e:
        logging.error(e)

@app.get("/rate")
async def get_rate(pair: str):
    """
    Retrieve the exchange rate between BTC/SAT to any given pair and viceversa

    Parameters:
        - **param1** (str)
        eg: btcusd, usdbtc, sathkd, eursat

    Returns:
        dict: {"rate":"1200.35"}
    """
    lenOfpair = len(pair)
    if lenOfpair != 6:
        return {"error": "Currency not found"}
    if 'btc' in pair:
        currency1 = pair[:3]
        currency2 = pair[3:]
        currency, inverse, sat = (currency2, False, False) if currency1 == "btc" else (currency1, True, False)
    elif 'sat' in pair:
        currency1 = pair[:3]
        currency2 = pair[3:]
        currency, inverse, sat = (currency2, False, True) if currency1 == "sat" else (currency1, True, True)
    try:
        if currency is None:
            return RedirectResponse('/', status_code=status.HTTP_302_FOUND)
        
        # _, rate = coindesk_btc_fiat(currency.upper())
        _, rate = coinbase_btc_fiat(currency.upper())


        if not inverse and not sat:
            btcfiat = "%.2f" % rate

        if inverse and not sat:
            btcfiat = 1/rate
            btcfiat = format(btcfiat, '.8f')

        if not inverse and sat:
            btcfiat = rate/10**8
            btcfiat = format(btcfiat, '.8f')

        if inverse and sat:
            btcfiat = (10**8)/rate
            btcfiat = format(btcfiat, '.2f')

        data = {"rate" : btcfiat}
        return data
    
    except Exception as e:
        logging.error(e)
        return {"error": "Failed to fetch exchange rate"}
        