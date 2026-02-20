from uuid import uuid4
from datetime import datetime, timezone

from .config import SHIPPING_TABLE_NAME
from .database import get_dynamodb_resource


class ShippingRepository:
    def __init__(self):
        dynamo_resource = get_dynamodb_resource()
        self.table = dynamo_resource.Table(SHIPPING_TABLE_NAME)

    def get_shipping(self, shipping_id: str):
        response = self.table.get_item(Key={"shipping_id": shipping_id})
        return response.get("Item")

    def create_shipping(self, shipping_type: str, product_ids: list, order_id: str, status: str, due_date: datetime):
        shipping_id = str(uuid4())
        item = {
            "shipping_id": shipping_id,
            "shipping_type": shipping_type,
            "order_id": str(order_id),
            "product_ids": ",".join(map(str, product_ids)),
            "shipping_status": status,
            "created_date": datetime.now(timezone.utc).isoformat(),
            "due_date": due_date.astimezone(timezone.utc).isoformat(),
        }
        self.table.put_item(Item=item)
        return shipping_id

    def update_shipping_status(self, shipping_id: str, status: str):
        response = self.table.update_item(
            Key={"shipping_id": shipping_id},
            UpdateExpression="SET shipping_status = :sh_status",
            ExpressionAttributeValues={":sh_status": status},
            ReturnValues="UPDATED_NEW",
        )
        return response
