# RATE API

The rate API is returns the BTC/USD, or other pair rate as a single value.

### Request

`GET /rate?pair=btcinr`

    curl -i -H 'Accept: application/json' http://localhost:8000/rate?pair=btcinr

### Response

    HTTP/1.1 200 OK
    date: Sun, 19 Nov 2023 07:47:00 GMT
    server: uvicorn
    content-length: 21
    content-type: application/json
    
    {"rate":"123.46"}
