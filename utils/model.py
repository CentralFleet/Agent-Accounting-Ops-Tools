from pydantic import BaseModel, Field
from typing import Optional, List, Union


## Item Model
class LineItem(BaseModel):
    item_id: str
    tax_id: str
    tax_name: str
    tax_type: str
    tax_percentage: float


## Invoice Model
class CustomField(BaseModel):
    customfield_id: str
    value: Optional[str] = None


class InvoiceObj(BaseModel):
    customer_id: str
    zcrm_potential_id: Union[int, str]
    reference_number: str
    custom_fields: List[CustomField]
    line_items: List[LineItem]


## Item Model
class ItemObj(BaseModel):
    name: str
    rate: float
    purchase_rate: float
    item_type: str
    custom_fields: List[CustomField]


## Bill Model
class BillCustomField(BaseModel):
    customfield_id: str
    value: Union[int, str]
    value_formatted: Optional[str] = None


class BillObj(BaseModel):
    vendor_id: str
    bill_number: str
    line_items: List[dict]
    custom_fields: List[BillCustomField]
