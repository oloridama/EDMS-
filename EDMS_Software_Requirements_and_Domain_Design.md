# Enterprise Distribution Management System (EDMS)

## Software Requirements & Domain Design Brief

## 1. Vision

EDMS will manage the lifecycle of automotive products from procurement through warehousing, inventory management, distribution, sales, logistics, returns, and reporting.

The primary objective is to provide a single source of truth for inventory and operations across branches while reducing manual errors and improving operational visibility.

## 2. Business Overview

The company imports automotive parts and lubricants primarily from China, stores inventory in a central Lagos warehouse, distributes inventory to regional branches, sells to retailers and end users, accepts orders through walk-ins, calls and WhatsApp, and uses internal logistics plus third-party couriers when necessary.

## 3. Business Goals

- Know current inventory levels across all locations.
- Prevent accepting orders for unavailable products.
- Track inventory movement between warehouses.
- Track customer orders and deliveries.
- Manage supplier purchases.
- Record damaged, expired and returned products.
- Produce operational and management reports.
- Support multiple user roles with different permissions.

## 4. Core Business Concepts

### Product

An item offered for sale. It owns identifying/catalog information such as SKU, name, description, brand, category and unit of measure.

**Product does not own inventory.**

### Supplier

A person or company from whom products are purchased. Suppliers can provide many products, and products may have multiple suppliers.

### Customer

A person or business purchasing products. Customers create sales orders.

### Branch

A business location. Examples include Lagos Central, Abuja and Port Harcourt. A branch may contain one or more warehouses.

### Warehouse

A physical storage location belonging to a branch. It receives, stores and releases inventory.

### Inventory

Represents the quantity and condition of products held by a warehouse at a given point in time. It can track available, reserved, damaged and expired quantities.

### Purchase Order

Created when the business decides to buy products.

Typical lifecycle:

`Draft → Approved → Sent → Partially Received → Completed`

### Sales Order

Created when a customer purchases products.

Typical lifecycle:

`Created → Paid → Picking → Packed → Dispatched → Delivered → Completed`

It supports partial fulfillment.

### Order Line

A single requested product and quantity within an order.

### Transfer Request

A request from one branch to another for stock redistribution. It is not a customer sale.

### Logistics

Coordinates movement of goods, including vehicles, couriers, drivers, dispatch and tracking.

### Dispatch

The act of releasing goods for transportation. It can originate from sales orders or transfer requests.

### Shipment

Represents the actual movement of goods after dispatch.

### Stock Movement

An event that changes inventory, such as receiving goods, a sale, branch transfer, customer return, supplier return, damage or disposal.

## 5. Major Business Workflows

### Procurement

Business identifies stock shortage  
→ Purchase Order created  
→ Supplier ships  
→ Warehouse receives  
→ Goods inspected  
→ Accepted goods added to inventory  
→ Rejected goods returned to supplier.

### Customer Sales

Customer places order  
→ Payment confirmed  
→ Inventory checked  
→ Products picked  
→ Products packed  
→ Dispatch created  
→ Shipment leaves warehouse  
→ Customer receives goods.

### Branch Transfer

Branch requests products  
→ Central warehouse reviews request  
→ Inventory reserved  
→ Dispatch created  
→ Shipment transported  
→ Receiving branch confirms receipt  
→ Inventory updated.

### Customer Return

Customer returns product  
→ Inspection performed  
→ Decision: restock, repair, return to supplier, dispose or refund.

## 6. User Roles

- CEO
- Administrator
- Branch Manager
- Warehouse Manager
- Cashier / Sales Officer
- Procurement Officer
- Logistics Officer
- Dispatch Rider

Each role will have different permissions.

## 7. Proposed Architecture

```text
app/
    administration/
    catalog/
    inventory/
    procurement/
    sales/
    logistics/
    reporting/
    shared/
```

Each business module owns its models, repositories and services.

## 8. Development Roadmap

1. **Catalog** — Products, Brands, Categories
2. **Administration** — Users, Roles, Branches, Warehouses
3. **Inventory** — Stock, Stock Movements
4. **Procurement** — Suppliers, Purchase Orders
5. **Sales** — Customers, Sales Orders, Order Lines
6. **Logistics** — Dispatch, Shipments, Transfers
7. **Reporting**
8. **API**
9. **Authentication**
10. **Testing**

## 9. Engineering Approach

We will design each module before implementing it.

1. Business discussion
2. Model design
3. Repository design
4. Service design
5. Tests
6. Code review
7. Refactoring
8. Meaningful Git commit

The domain model is expected to evolve as implementation reveals missing or incorrect assumptions. Documentation will be updated rather than relying on memory.

## 10. Current Assignment — Catalog Module

Build the first bounded context: **Product Catalog**.

Its responsibility is only to answer:

> “What products does the company sell?”

It should **not** manage inventory, warehouses, orders or suppliers.

### Initial Structure

```text
catalog/
    models/
        product.py
        category.py
        brand.py

    repositories/
        product_repository.py

    services/
        product_service.py
```

### Assignment

Design:

- `Product`
- `ProductCategory`
- `Brand`

Then define:

- `ProductRepository` interface
- `ProductService` business rules

Do **not** implement every method immediately. Focus on making the boundaries and responsibilities clear.
