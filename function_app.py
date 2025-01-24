import azure.functions as func
import logging
import json
from src.funcmain import *

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="v1/invoice/create")
async def create_invoice(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Create Invoice request received')
    body = req.get_json()
    logging.info(body)
    result = process_invoice(body=body)
    return func.HttpResponse(json.dumps(result), status_code=result['code'])


@app.route(route="v1/bill/create")
async def create_bill(req: func.HttpRequest) -> func.HttpResponse:
    logging.info("Create Bill request received")
    body = req.get_json()
    logging.info(body)
    result = process_bill(body=body)
    return func.HttpResponse(json.dumps(result), status_code=result['code'])


@app.route(route="ping", methods=['GET','POST'])
async def ping(req: func.HttpRequest) -> func.HttpResponse:
    logging.info(f'Request received from {req.url}')
    logging.info('Ping request received.')
    return func.HttpResponse("Service is up", status_code=200)
