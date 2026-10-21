import os
import shutil
import tempfile
import unittest
from decimal import Decimal

from fastapi.testclient import TestClient

from API.main import create_app


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        database_url = f"sqlite:///{os.path.join(self.tmpdir, 'test.db')}"
        self.app = create_app(database_url)
        self.client = TestClient(self.app)

    def tearDown(self):
        self.client.close()
        self.app.state.database.engine.dispose()
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    # --- helpers ---------------------------------------------------------
    def bootstrap(self):
        response = self.client.post(
            "/api/auth/bootstrap",
            json={
                "username": "admin",
                "email": "admin@example.com",
                "password": "secret123",
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def login(self, username="admin", password="secret123"):
        response = self.client.post(
            "/api/auth/login",
            json={"username": username, "password": password},
        )
        self.assertEqual(response.status_code, 200, response.text)
        return response.json()["access_token"]

    @staticmethod
    def auth(token):
        return {"Authorization": f"Bearer {token}"}

    def seed_catalog(self, token):
        response = self.client.post(
            "/api/catalog/categories",
            json={
                "name": "Parts",
                "description": "Automotive parts",
                "specification_types": [
                    {"name": "Color", "value_type": "text", "allowed_values": []}
                ],
            },
            headers=self.auth(token),
        )
        self.assertEqual(response.status_code, 201, response.text)

        response = self.client.post(
            "/api/catalog/products",
            json={
                "product_id": "P-1",
                "name": "Oil Filter",
                "description": "Spin-on filter",
                "brand_name": "Acme",
                "category_name": "Parts",
            },
            headers=self.auth(token),
        )
        self.assertEqual(response.status_code, 201, response.text)

        response = self.client.post(
            "/api/catalog/configurations",
            json={
                "product_id": "P-1",
                "specifications": {"Color": "Red"},
                "pricing_rules": [
                    {"min_quantity": 1, "max_quantity": None, "unit_price": "5.00"}
                ],
            },
            headers=self.auth(token),
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()["configuration_id"]

    # --- tests -----------------------------------------------------------
    def test_health(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

    def test_bootstrap_runs_once_and_me_requires_a_token(self):
        self.bootstrap()
        user = self.bootstrap_error = self.client.post(
            "/api/auth/bootstrap",
            json={
                "username": "second",
                "email": "second@example.com",
                "password": "secret123",
            },
        )
        self.assertEqual(user.status_code, 403)

        unauthorized = self.client.get("/api/auth/me")
        self.assertEqual(unauthorized.status_code, 401)

        token = self.login()
        me = self.client.get("/api/auth/me", headers=self.auth(token))
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()["role"], "administrator")
        self.assertIn("auth:manage", me.json()["permissions"])

    def test_invalid_credentials_and_token_are_rejected(self):
        self.bootstrap()

        bad_login = self.client.post(
            "/api/auth/login",
            json={"username": "admin", "password": "wrong-password"},
        )
        self.assertEqual(bad_login.status_code, 401)

        bad_token = self.client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer not-a-real-token"},
        )
        self.assertEqual(bad_token.status_code, 401)

    def test_catalog_inventory_sales_and_reporting_flow(self):
        self.bootstrap()
        token = self.login()
        configuration_id = self.seed_catalog(token)

        lot = self.client.post(
            "/api/inventory/lots",
            json={
                "lot_id": "LOT-1",
                "configuration_id": configuration_id,
                "warehouse_id": "WH-1",
                "quantity": 10,
            },
            headers=self.auth(token),
        )
        self.assertEqual(lot.status_code, 201, lot.text)

        order = self.client.post(
            "/api/sales/orders",
            json={
                "customer": {"customer_id": "C-1", "name": "Retailer"},
                "warehouse_id": "WH-1",
                "lines": [{"configuration_id": configuration_id, "quantity": 2}],
            },
            headers=self.auth(token),
        )
        self.assertEqual(order.status_code, 201, order.text)
        created = order.json()
        self.assertEqual(created["status"], "created")
        self.assertEqual(Decimal(created["total"]), Decimal("10.00"))

        paid = self.client.post(
            f"/api/sales/orders/{created['order_id']}/pay",
            headers=self.auth(token),
        )
        self.assertEqual(paid.status_code, 200, paid.text)
        self.assertEqual(paid.json()["status"], "paid")

        stock = self.client.get(
            f"/api/inventory/stock/{configuration_id}",
            params={"warehouse_id": "WH-1"},
            headers=self.auth(token),
        )
        self.assertEqual(stock.status_code, 200)
        self.assertEqual(stock.json()["available_quantity"], 8)

        sales_report = self.client.get("/api/reports/sales", headers=self.auth(token))
        self.assertEqual(sales_report.status_code, 200)
        self.assertEqual(sales_report.json()[0]["status"], "paid")

    def test_role_permissions_are_enforced(self):
        self.bootstrap()
        admin_token = self.login()

        registered = self.client.post(
            "/api/auth/register",
            json={
                "username": "officer",
                "email": "officer@example.com",
                "password": "secret123",
                "role": "sales_officer",
            },
            headers=self.auth(admin_token),
        )
        self.assertEqual(registered.status_code, 201, registered.text)

        officer_token = self.login("officer")
        forbidden_write = self.client.post(
            "/api/catalog/categories",
            json={"name": "Hidden", "specification_types": []},
            headers=self.auth(officer_token),
        )
        self.assertEqual(forbidden_write.status_code, 403)

        forbidden_report = self.client.get(
            "/api/reports/inventory",
            headers=self.auth(officer_token),
        )
        self.assertEqual(forbidden_report.status_code, 403)

        allowed_read = self.client.get(
            "/api/inventory/stock/1",
            params={"warehouse_id": "WH-1"},
            headers=self.auth(officer_token),
        )
        self.assertEqual(allowed_read.status_code, 200)

    def test_domain_errors_map_to_client_errors(self):
        self.bootstrap()
        token = self.login()

        response = self.client.post(
            "/api/sales/orders",
            json={
                "customer": {"customer_id": "C-1", "name": "Retailer"},
                "warehouse_id": "WH-1",
                "lines": [{"configuration_id": 999, "quantity": 1}],
            },
            headers=self.auth(token),
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("999", response.json()["detail"])

    def test_procurement_and_logistics_flow(self):
        self.bootstrap()
        token = self.login()
        configuration_id = self.seed_catalog(token)

        purchase_order = self.client.post(
            "/api/procurement/orders",
            json={
                "supplier": {
                    "name": "Acme Supply",
                    "address": "Lagos",
                    "email": "supply@example.com",
                    "phone": "555",
                },
                "lines": [
                    {
                        "configuration_id": configuration_id,
                        "quantity": 5,
                        "manufacturer_name": "Acme",
                        "unit_price": "4.00",
                    }
                ],
            },
            headers=self.auth(token),
        )
        self.assertEqual(purchase_order.status_code, 201, purchase_order.text)
        order_id = purchase_order.json()["order_id"]

        approved = self.client.patch(
            f"/api/procurement/orders/{order_id}/status",
            json={"status": "approved"},
            headers=self.auth(token),
        )
        self.assertEqual(approved.status_code, 200, approved.text)
        self.assertEqual(approved.json()["status"], "approved")

        transporter = self.client.post(
            "/api/logistics/transporters",
            json={
                "name": "Courier Co",
                "contact_number": "555",
                "email": "courier@example.com",
                "address": "Lagos",
                "transportation_type": "road",
            },
            headers=self.auth(token),
        )
        self.assertEqual(transporter.status_code, 201, transporter.text)
        transporter_id = transporter.json()["transporter_id"]

        shipment = self.client.post(
            "/api/logistics/shipments",
            json={
                "tracking_id": "TRK-1",
                "configuration_ids": [configuration_id],
                "transporter_id": transporter_id,
                "transporter_name": "Courier Co",
                "mode_of_transport": {
                    "name": "Van",
                    "reg_no": "REG-1",
                    "length": 1.0,
                    "width": 2.0,
                    "height": 3.0,
                },
            },
            headers=self.auth(token),
        )
        self.assertEqual(shipment.status_code, 201, shipment.text)
        self.assertEqual(shipment.json()["configuration_ids"], [configuration_id])

        in_transit = self.client.patch(
            "/api/logistics/shipments/TRK-1/status",
            json={"status": "In Transit"},
            headers=self.auth(token),
        )
        self.assertEqual(in_transit.status_code, 200, in_transit.text)
        self.assertEqual(in_transit.json()["status"], "In Transit")


if __name__ == "__main__":
    unittest.main()
