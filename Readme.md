# Invoice and Billing Management

This project contains Azure Functions for managing invoices and bills using Zoho Books and Zoho CRM APIs.

## Endpoints

### 1. **Create Invoice**
**Route:** `v1/invoice/create`  
**Method:** `POST`  
**Description:**  
Processes and creates invoices in Zoho Books for a given deal and associated vehicles.  

**Request Body:**  
```json
{
    "deal_id": "string",
    "order_id": "string",
    "Customer_Price_Excl_Tax": "float",
    "Carrier_Fee": "float",
    "Tax_ID": "string",
    "Tax_Name": "string",
    "Tax_Type": "string",
    "Tax_Rate": "float",
    "Customer_id": "string",
    "vendor_name": "string",
    "PickupLocation": "string",
    "Drop_off_Location": "string",
    "special_instruction": "string"
}
```
**Response:**
```json
{
    "code": 200,
    "message": "Invoice created successfully",
    "status": "success"
}
```

### 2. **Create Bill**
**Route:** `v1/bill/create`
**Method:** `POST`
**Description:**
Processes and creates bills in Zoho CRM for a given deal and associated vehicles.

**Request Body:**
```json
{
    "deal_id": "string",
    "order_id": "string",
    "Customer_Price_Excl_Tax": "float",
    "Carrier_Fee": "float",
    "vendor_id": "string"
}
```

**Response:**
```json
{
    "code": 200,
    "message": "Bill created successfully",
    "status": "success"
}
```



## 🛠️ Contributing Guide  

Thank you for considering contributing to this project! Follow these steps to get started:  

### 🚀 Steps to Contribute  

1. **Fork the Repository**  
   Click the **Fork** button at the top right of this repository to create your own copy.  

2. **Clone Your Fork**  
   ```sh
   git clone https://github.com/CentralFleet/Agent-Accounting-Ops-Tools.git
   cd Agent-Accounting-Ops-Tools
   ```
3. **Create a New Branch**
   ```sh
   git checkout -b your-branch-name
   ```
4. **Make Your Changes**
    Make your changes and commit them to your local branch

5. **Push Your Changes**
    ```sh
    git push origin your-branch-name
    ```