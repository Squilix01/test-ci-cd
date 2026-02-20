import uuid
import random
import boto3
import pytest
from datetime import datetime, timedelta, timezone

from app.eshop import Product, ShoppingCart, Order, Shipment
from services import ShippingService
from services.repository import ShippingRepository
from services.publisher import ShippingPublisher
from services.config import AWS_ENDPOINT_URL, AWS_REGION, SHIPPING_QUEUE


# ----------------------------
# TOP-DOWN (mock dependencies)
# ----------------------------

@pytest.mark.parametrize("order_id, shipping_id", [
    ("order_1", "shipping_1"),
    ("order_i2hur2937r9", "shipping_1!!!!"),
    (str(uuid.uuid4()), str(uuid.uuid4()))
])
def test_place_order_with_mocked_repo(mocker, order_id, shipping_id):
    mock_repo = mocker.Mock()
    mock_publisher = mocker.Mock()
    shipping_service = ShippingService(mock_repo, mock_publisher)
    mock_repo.create_shipping.return_value = shipping_id

    cart = ShoppingCart()
    cart.add_product(Product("Product", random.random() * 10000, 10), 9)

    order = Order(cart, shipping_service, order_id)
    due_date = datetime.now(timezone.utc) + timedelta(seconds=10)

    actual_shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=due_date
    )

    assert actual_shipping_id == shipping_id

    mock_repo.create_shipping.assert_called_once()
    mock_publisher.send_new_shipping.assert_called_once_with(shipping_id)
    mock_repo.update_shipping_status.assert_called_once_with(shipping_id, shipping_service.SHIPPING_IN_PROGRESS)


def test_create_shipping_unavailable_type_topdown(mocker):
    mock_repo = mocker.Mock()
    mock_publisher = mocker.Mock()
    service = ShippingService(mock_repo, mock_publisher)

    with pytest.raises(ValueError):
        service.create_shipping("РќР•Р†РЎРќРЈР®Р§РР™ РўРРџ", ["P1"], "order_1", datetime.now(timezone.utc) + timedelta(minutes=1))

    mock_repo.create_shipping.assert_not_called()
    mock_publisher.send_new_shipping.assert_not_called()


def test_create_shipping_due_date_in_past_topdown(mocker):
    mock_repo = mocker.Mock()
    mock_publisher = mocker.Mock()
    service = ShippingService(mock_repo, mock_publisher)

    with pytest.raises(ValueError):
        service.create_shipping(
            ShippingService.list_available_shipping_type()[0],
            ["P1"], "order_1",
            datetime.now(timezone.utc) - timedelta(seconds=1)
        )

    mock_repo.create_shipping.assert_not_called()
    mock_publisher.send_new_shipping.assert_not_called()


def test_create_shipping_happy_path_topdown(mocker):
    mock_repo = mocker.Mock()
    mock_publisher = mocker.Mock()
    service = ShippingService(mock_repo, mock_publisher)

    shipping_id = "ship_123"
    mock_repo.create_shipping.return_value = shipping_id

    due = datetime.now(timezone.utc) + timedelta(minutes=1)
    result = service.create_shipping(ShippingService.list_available_shipping_type()[0], ["P1"], "order_9", due)

    assert result == shipping_id
    mock_repo.create_shipping.assert_called_once()
    mock_publisher.send_new_shipping.assert_called_once_with(shipping_id)
    mock_repo.update_shipping_status.assert_called_once_with(shipping_id, service.SHIPPING_IN_PROGRESS)


# -------------------------------------
# REAL INTEGRATION (LocalStack + boto3)
# -------------------------------------

def _get_queue_url():
    sqs_client = boto3.client(
        "sqs",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    return sqs_client.get_queue_url(QueueName=SHIPPING_QUEUE)["QueueUrl"]


def test_place_order_with_unavailable_shipping_type_fails():
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())

    cart = ShoppingCart()
    cart.add_product(Product("Product", random.random() * 10000, 10), 9)

    order = Order(cart, shipping_service)

    with pytest.raises(ValueError) as excinfo:
        order.place_order("РќРѕРІРёР№ С‚РёРї РґРѕСЃС‚Р°РІРєРё", due_date=datetime.now(timezone.utc) + timedelta(seconds=10))

    assert "Shipping type is not available" in str(excinfo.value)


def test_when_place_order_then_shipping_in_queue():
    shipping_service = ShippingService(ShippingRepository(), ShippingPublisher())
    cart = ShoppingCart()
    cart.add_product(Product("Product", random.random() * 10000, 10), 1)

    order = Order(cart, shipping_service)
    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    sqs_client = boto3.client("sqs", endpoint_url=AWS_ENDPOINT_URL, region_name=AWS_REGION, aws_access_key_id="test", aws_secret_access_key="test")
    queue_url = _get_queue_url()

    response = sqs_client.receive_message(QueueUrl=queue_url, MaxNumberOfMessages=1, WaitTimeSeconds=10)
    messages = response.get("Messages", [])

    assert len(messages) >= 1
    assert shipping_id in [m["Body"] for m in messages]


def test_when_place_order_then_shipping_saved_in_dynamodb():
    repo = ShippingRepository()
    publisher = ShippingPublisher()
    service = ShippingService(repo, publisher)

    cart = ShoppingCart()
    cart.add_product(Product("Product", 100, 10), 1)
    order = Order(cart, service)

    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    item = repo.get_shipping(shipping_id)
    assert item is not None
    assert item["shipping_id"] == shipping_id
    assert item["shipping_status"] in [service.SHIPPING_IN_PROGRESS, service.SHIPPING_CREATED]


def test_check_status_returns_current_status():
    repo = ShippingRepository()
    publisher = ShippingPublisher()
    service = ShippingService(repo, publisher)

    cart = ShoppingCart()
    cart.add_product(Product("Product", 100, 10), 1)
    order = Order(cart, service)

    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=1)
    )

    status = service.check_status(shipping_id)
    assert status in [service.SHIPPING_IN_PROGRESS, service.SHIPPING_COMPLETED, service.SHIPPING_FAILED, service.SHIPPING_CREATED]


def test_process_shipping_completes_when_due_date_in_future():
    repo = ShippingRepository()
    publisher = ShippingPublisher()
    service = ShippingService(repo, publisher)

    cart = ShoppingCart()
    cart.add_product(Product("Product", 100, 10), 1)
    order = Order(cart, service)

    shipping_id = order.place_order(
        ShippingService.list_available_shipping_type()[0],
        due_date=datetime.now(timezone.utc) + timedelta(minutes=2)
    )

    meta = service.process_shipping(shipping_id)
    assert "HTTPStatusCode" in meta  # ResponseMetadata
    assert service.check_status(shipping_id) == service.SHIPPING_COMPLETED


def test_process_shipping_fails_when_due_date_in_past():
    repo = ShippingRepository()
    publisher = ShippingPublisher()
    service = ShippingService(repo, publisher)

    # РЎРѕР·РґР°РµРј shipping РЅР°РїСЂСЏРјСѓСЋ С‡РµСЂРµР· СЂРµРїРѕР·РёС‚РѕСЂРёР№, С‡С‚РѕР±С‹ РёР·РЅР°С‡Р°Р»СЊРЅРѕ due_date Р±С‹Р»Рѕ РІ РїСЂРѕС€Р»РѕРј
    shipping_id = repo.create_shipping(
        ShippingService.list_available_shipping_type()[0],
        ["Product"],
        "order_zzz",
        service.SHIPPING_IN_PROGRESS,
        datetime.now(timezone.utc) - timedelta(seconds=1)
    )

    meta = service.process_shipping(shipping_id)
    assert "HTTPStatusCode" in meta
    assert service.check_status(shipping_id) == service.SHIPPING_FAILED

