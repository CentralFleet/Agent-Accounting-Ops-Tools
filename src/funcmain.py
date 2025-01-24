# src/funcmain.py
from utils.model import *
from utils.helpers import *
import os
import logging
from pyzohobook import (Bill, Invoice, 
                        Item, Vendor, 
                        Customer, TokenManager 
                        )
from pyzohocrm import ZohoApi, token_manager
from time import sleep



TOKEN_BOOK = TokenManager()


TOKEN_CRM = token_manager.TokenManager(
    "canada",
    refresh_token=os.getenv("ZOHO_CRM_REFRESH_TOKEN"),
    client_id=os.getenv("ZOHO_CRM_CLIENT_ID"),
    client_secret=os.getenv("ZOHO_CRM_CLIENT_SECRET"),
    grant_type="refresh_token",
    token_filename="token_crm.json",
    token_dir=os.getenv("ZOHO_TOKEN_DIR")
)

def handle_invoice_creation(deal_id, account_id, item_id, body, book_token,uniqueid) -> dict:
    """
    Creates an invoice in Zoho Books.

    Args:
        deal_id (str): The ID of the deal in Zoho CRM.
        account_id (str): The customer account ID in Zoho Books.
        item_id (str): The ID of the item to be invoiced.
        body (dict): Dictionary containing invoice details.
        book_token (str): Access token for Zoho Books.

    Returns:
        dict: Response from Zoho Books API or error details.
    """

    custom_fields = [
        CustomField(customfield_id="30379000000302087", value=body.get("PickupLocation")),
        CustomField(customfield_id="30379000000302093", value=body.get("Drop_off_Location")),
        CustomField(customfield_id="30379000000541041", value=body.get("special_instruction")),
        CustomField(customfield_id="30379000000684021", value=uniqueid)
    ]

    line_items = [
        LineItem(
            item_id=item_id,
            tax_id=body.get("Tax_ID"),
            tax_name=body.get("Tax_Name"),
            tax_type=body.get("Tax_Type"),
            tax_percentage=body.get("Tax_Rate")
        )
    ]

    invoice_obj = InvoiceObj(
        customer_id=account_id,
        zcrm_potential_id=str(deal_id),
        reference_number=body.get("order_id"),
        custom_fields=custom_fields,
        line_items=line_items
    )

    invoice_resp = Invoice.create_invoice(invoice_obj.dict(), book_token)
    return invoice_resp


def handle_bill_creation(index, deal_id, item_id, vendor_book_id, body, book_token) -> dict:
    """
    Creates a bill in Zoho Books.

    Args:
        index (int): Index of the current item in a list.
        deal_id (str): The ID of the deal in Zoho CRM.
        item_id (str): The ID of the item to be billed.
        vendor_book_id (str): The vendor ID in Zoho Books.
        body (dict): Dictionary containing bill details.
        book_token (str): Access token for Zoho Books.

    Returns:
        dict: Response from Zoho Books API or error details.
    """

    bill_number = f"{body.get('order_id')} - {index}"
    bill_custom_fields = [
        BillCustomField(
            customfield_id="30379000000295115",
            value=deal_id,
            value_formatted=body.get('order_id')
        )
    ]

    bill_obj = BillObj(
        vendor_id=vendor_book_id,
        bill_number=bill_number,
        line_items=[{"item_id": item_id}],
        custom_fields=bill_custom_fields
    )

    bill_resp = Bill.create_bill(bill_obj.dict(), book_token)
    return bill_resp

def process_item(vehicle : dict, price : str, book_token : str, organization_id : str, carrier_fee : int) -> dict:
    """
    Creates or retrieves an item in Zoho Books.

    Args:
        vehicle (dict): Vehicle details (e.g., Year, Make, Model, VIN).
        price (float): Price of the item.
        book_token (str): Access token for Zoho Books.
        organization_id (str): Organization ID for Zoho Books.
        carrier_fee (float): Purchase rate for the carrier.

    Returns:
        dict: Result of the item creation or retrieval process.
    """

    item_name = f"{vehicle['Year']}-{vehicle['Make']}-{vehicle['Model']}-{vehicle['VIN']}"
    custom_fields = [
        CustomField(customfield_id="30379000000302001", value=vehicle.get("Make")),
        CustomField(customfield_id="30379000000302021", value=vehicle.get("Model")),
        CustomField(customfield_id="30379000000302067", value=vehicle.get("VIN")),
        CustomField(customfield_id="30379000000302041", value=vehicle.get("Year")),
    ]

    item_obj = ItemObj(
        name=item_name,
        rate=price,
        item_type="sales_and_purchases",
        purchase_rate=carrier_fee,
        custom_fields=custom_fields,
    )

    created_item = Item.create_item(item_obj.dict(), book_token)

    if created_item.status_code != 201:
        if created_item.json().get("code") == 1001:
            item_id = Item.search_item(item_name, book_token).json().get("items", [])[0].get("item_id")
            return {
                "code": 200,
                "item_id": item_id,
                "message": "Item already exists, retrieved item_id"
            }
        else:
            return {
                "code": created_item.status_code,
                "message": "Internal Server Error"
            }

    item_id = created_item.json().get("item", {}).get("item_id")

    return {
        "code": 200,
        "item_id": item_id,
        "message": "Item created successfully"
    }


def process_invoice(body: dict) -> int:
    invoice_count = 0
    deal_id = body.get("deal_id")
    order_id = body.get("order_id")
    book_token = TOKEN_BOOK.get_access_token()
    crm_token = TOKEN_CRM.get_access_token()

    vehicle_response = ZohoApi(base_url="https://www.zohoapis.ca/crm/v2").fetch_related_list(
        moduleName="Deals", record_id=deal_id, name="Vehicles", token=crm_token
    )
    vehicles = vehicle_response.json().get("data", [])
    
    for i, vehicle in enumerate(vehicles):
        data = process_item(vehicle, body.get("Customer_Price_Excl_Tax"), book_token, os.getenv("ORGANIZATION_ID"), body.get("Carrier_Fee"))
        if data['code'] != 200:
            raise Exception(data['message'])
        item_id = data['item_id']

        customer_id = body.get("Customer_id")
        customer_account = Customer.search_customer(
            search_params={"zcrm_account_id": customer_id},
            book_token=book_token
        )
        customer_data = customer_account.json().get("contacts", [])[0]
        account_id = customer_data["contact_id"]

        resp = handle_invoice_creation(deal_id, account_id, item_id, body, book_token, uniqueid=f"{order_id}-{i}")
        if resp.status_code != 201:
            if resp.json().get("code") == 120303:
                send_message_to_channel(os.getenv("SLACK_CHANNEL_ID"), f":warning: Internal Server Warning. \n *Details* \n - OrderID: `{order_id}` \n - Message: `{resp.json()}` \n - Origin: Billing Service")
                logging.info("Invoice already exists, skipping creation")
                continue
            raise Exception(resp.json())
        invoice_count += 1

    if invoice_count == len(vehicles) and invoice_count > 0:
        code, message = combine_invoices_and_upload(crm_token, book_token, deal_id, order_id)
        if code != 200:
            raise Exception(message)
        
        return {"status":"success","message":"Invoices created successfully","invoice_count": invoice_count,"code":200}

    else:

        return {"status":"failed","message":"Failed to create invoices","invoice_count": invoice_count,"code":500}


def process_bill(body: dict) -> int:
    bill_count = 0
    deal_id = body.get("deal_id")
    order_id = body.get("order_id")
    book_token = TOKEN_BOOK.get_access_token()
    crm_token = TOKEN_CRM.get_access_token()

    vehicle_response = ZohoApi(base_url="https://www.zohoapis.ca/crm/v2").fetch_related_list(
        moduleName="Deals", record_id=deal_id, name="Vehicles", token=crm_token
    )
    vehicles = vehicle_response.json().get("data", [])
    for index, vehicle in enumerate(vehicles):
        data = process_item(vehicle, body.get("Customer_Price_Excl_Tax"), book_token, os.getenv("ORGANIZATION_ID"), body.get("Carrier_Fee"))
        if data['code'] != 200:
            raise Exception(data['message'])
        item_id = data['item_id']
        ## update purchase rate to carrier fee
        Item.update_item(
            item_id=item_id,
            item_data={ "purchase_rate": body.get("Carrier_Fee") },
            book_token=book_token)

        vendor_name = body.get("vendor_name")
        vendor_response = Vendor.search_vendor(
            search_params={"vendor_name": vendor_name},
            book_token=book_token
        )
        vendor_data = vendor_response.json().get("contacts", [])[0]
        vendor_book_id = vendor_data["contact_id"]

        resp = handle_bill_creation(index, deal_id, item_id, vendor_book_id, body, book_token)
        if resp.status_code != 201:
            if resp.json().get("code") == 13011:
                send_message_to_channel(os.getenv("SLACK_CHANNEL_ID"), f":warning: Internal Server Warning. \n *Details* \n -OrderID: `{order_id}` \n - Message: `{resp.json()}` \n - Origin: Billing Service")
                logging.info("Bill already exists, skipping creation")
                continue
            raise Exception(resp.json())
        bill_count += 1


    if bill_count == len(vehicles):
        send_message_to_channel(os.getenv("BILL_CHANNEL_ID"), f":white_check_mark: Bill created successfully! \n *Details*: \n - Order id: `{order_id}` \n - Billed Amount: `CAD {body.get('Carrier_Fee')}` \n - Bill Count: `{bill_count}`")
        return {"status":"success","message":"Bills created successfully","bill_count": bill_count,"code":200}
    
    else:
    
        return {"status":"failed","message":"Failed to create bills","bill_count": bill_count,"code":500}



def combine_invoices_and_upload(access_token : str, book_token : str, deal_id : str, reference_id : str):
    try:
        
        def download_pdf(invoice_id, book_token):
            """
            Downloads the PDF for a given invoice ID.

            Args:
                invoice_id (str): Invoice ID in Zoho Books.
                book_token (str): Access token for Zoho Books.

            Returns:
                str: File path of the downloaded PDF or None in case of failure.
            """
            try_count = 0
            max_retry = 3
            delay = 2 + try_count
            while try_count < max_retry:
                try:
                    logging.info(f"Downloading invoice {invoice_id}")
                    response = Invoice.fetch_invoice(invoice_id=invoice_id, book_token=book_token, formate="pdf")

                    logging.info(f"Response: {response}")
                    response.raise_for_status()
                    file_path = os.path.join(os.getenv("ZOHO_TOKEN_DIR"), f"invoice_{invoice_id}.pdf")
                    logging.info(f"File path: {file_path}")

                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    logging.info(f"Invoice {invoice_id} downloaded successfully to {file_path}.")
                    return file_path
                
                except ConnectionError as ce:
                    try_count += 1
                    sleep(delay)
                    logging.error(f"Connection error: {ce}")
                    continue

                except Exception as e:
                    logging.error(f"Failed to download invoice {invoice_id}: {e}")
                    return None
            

        search_resp = Invoice.search_invoice(
            search_params={"reference_number": reference_id},
            book_token=book_token,
        
            )
        
        invoice_ids = [invoice['invoice_id'] for invoice in search_resp.json().get("invoices", [])]

        logging.info(f"Number of invoice found: {len(invoice_ids)}")

        pdf_paths = []
        for invoice_id in invoice_ids:
            pdf_path = download_pdf(invoice_id, book_token)
            Invoice.mark_invoice(book_token=book_token, invoice_id=invoice_id, status="sent")
            pdf_paths.append(pdf_path)

        logging.info(f"PDF paths: {pdf_paths}")
        output_filename= f"INVOICE-{reference_id}.pdf"
        output_path = os.path.join(os.getenv("ZOHO_TOKEN_DIR"), output_filename)
        merge_pdfs(pdf_paths, output_path)
        ## attach pdf to deal attachment related list

        
        invoice_upload_resp = ZohoApi(base_url="https://www.zohoapis.ca/crm/v2").attach_file(
            moduleName="Deals",
            record_id=deal_id,
            file_path=output_path,
            token=access_token
            )
        
        if invoice_upload_resp.status_code == 200:
            upload_invoice_to_slack(output_path, os.getenv("INVOICE_CHANNEL_ID"), os.getenv("SLACK_BOT_TOKEN"),comment=f":white_check_mark: Invoice created and attached successfully! \n *Details* \n - Order id: `{reference_id}` \n - Invoiced Amount (per vehicle): `CAD {search_resp.json().get('invoices')[0].get('total')}` \n - Invoice Count: `{len(invoice_ids)}`")
        
        os.remove(output_path)
        return invoice_upload_resp.status_code, str(invoice_upload_resp.json())
    except Exception as e:
        logging.error(f"Error combining invoices: {str(e)}")
        return 500, str(e)