# Order Service API Documentation

## 1. Overview

The Order Service is a Flask-based microservice responsible for processing book purchases in the Bazar Distributed Online Bookstore.

It communicates with the Catalog Service to retrieve book information and deduct stock. It uses SQLite to store purchase orders and their processing statuses.

**Service Port:** `5002`

**Base URL (local):** `http://localhost:5002`

## 2. Health Check

**Endpoint:** `GET /health`

Checks whether the Order Service is running.

**Success Response — HTTP 200**

```json
{
  "service": "order",
  "status": "ok"
}
```

## 3. Purchase a Book

**Endpoint:** `POST /purchase`

**Content-Type:** `application/json`

Creates and processes a book purchase.

### Request Body

```json
{
  "item_number": 1,
  "quantity": 1,
  "request_id": "purchase-001"
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|---|---|---|---|
| `item_number` | Integer | Yes | Positive book identifier |
| `quantity` | Integer | No | Positive quantity; defaults to 1 |
| `request_id` | String | Yes | Unique, non-empty request identifier, maximum 128 characters |

### Successful Purchase — HTTP 201

```json
{
  "message": "Purchase completed successfully",
  "order": {
    "...": "Saved order details"
  }
}
```

The `order` object is retrieved from the Order Service database. Its exact fields depend on the `get_order()` implementation.

## 4. Purchase Processing Workflow

1. Validate the incoming JSON request.
2. Create an order record using the unique `request_id`.
3. Check whether the request was previously processed.
4. Claim the order for processing.
5. Retrieve book information from the Catalog Service using `GET /info/<item_number>`.
6. Verify the book data and available stock.
7. Calculate the unit price and total price.
8. Request an atomic stock decrement through `PATCH /books/<item_number>/decrement`.
9. Mark the order as completed and store its pricing information.
10. Return the purchase result.

## 5. Duplicate Request Handling

The `request_id` is used to prevent repeated stock deductions for the same purchase request.

**Duplicate completed request — HTTP 200**

```json
{
  "message": "Order already completed",
  "order": {
    "...": "Existing order details"
  }
}
```

**Existing request that is not completed — HTTP 202**

```json
{
  "message": "Order already exists; no new stock deduction attempted",
  "order": {
    "...": "Existing order details"
  }
}
```

**Same request ID with different purchase data — HTTP 409**

```json
{
  "error": "request_id already used for different purchase data"
}
```

The service does not attempt a second stock deduction for an existing request ID.

## 6. Error Handling

| HTTP Status | Condition |
|---|---|
| `400` | Missing or invalid JSON, request ID, book ID, or quantity |
| `404` | Book does not exist |
| `409` | Insufficient stock or conflicting request ID |
| `502` | Unexpected Catalog Service response or uncertain stock deduction result |
| `503` | Order database unavailable, Catalog Service communication failure, or order processing/finalization failure |

### Example: Insufficient Stock — HTTP 409

```json
{
  "error": "Insufficient stock",
  "available_stock": 5
}
```

When the atomic stock decrement itself returns HTTP 409, the response contains only the `error` field.

### Example: Book Not Found — HTTP 404

```json
{
  "error": "Book not found"
}
```

### Example: Invalid Quantity — HTTP 400

```json
{
  "error": "quantity must be a positive integer"
}
```

## 7. Order Statuses

The Order Service uses the following statuses during purchase processing:

- **pending:** Order has been created but has not yet been claimed for processing.
- **processing:** Order is being processed.
- **completed:** Purchase succeeded and the order was finalized.
- **failed:** Purchase failed.
- **uncertain:** Stock deduction may have occurred, but its result could not be confirmed.

An uncertain order requires investigation before attempting another purchase.

## 8. Database

The Order Service uses a local SQLite database to store order records.

**Database file:** `orders.db`

Database operations are implemented in `database.py`, including:

- `initialize_database()`
- `create_order()`
- `get_order()`
- `claim_order()`
- `update_order_status()`

## 9. Inter-Service Communication

The Order Service communicates with the Catalog Service over HTTP.

The Catalog Service address is configured using:

`CATALOG_SERVICE_URL`

**Default:** `http://127.0.0.1:5001`

The Order Service uses:

- `GET /info/<item_number>` to retrieve book information.
- `PATCH /books/<item_number>/decrement` to reduce available stock.

Both HTTP requests use a five-second timeout.

## 10. Testing Examples

### Health Check

```bash
curl -i http://localhost:5002/health
```

### Successful Purchase

```bash
curl -i -X POST http://localhost:5002/purchase \
  -H "Content-Type: application/json" \
  -d '{"item_number":1,"quantity":1,"request_id":"order-doc-test-001"}'
```

**Important:** This purchase example modifies actual stock and creates an order. Use it only when a test purchase is intended.

### Duplicate Purchase

Repeat the previous request using the same `request_id` and purchase data. A completed order should return HTTP 200 without another stock deduction.

### Nonexistent Book

```bash
curl -i -X POST http://localhost:5002/purchase \
  -H "Content-Type: application/json" \
  -d '{"item_number":9999,"quantity":1,"request_id":"order-doc-missing-001"}'
```

Expected response: HTTP 404.

## 11. Reliability Considerations

The Catalog Service performs an atomic stock decrement, which helps prevent overselling during concurrent purchases.

The Order Service uses unique request identifiers to avoid repeated deductions caused by duplicate requests.

However, the order database and Catalog database are separate. Their updates are not part of one distributed transaction. A stock deduction can succeed even if order finalization subsequently fails.

The service explicitly reports uncertain outcomes in some failure scenarios. These situations require manual reconciliation rather than automatic retries with a new request ID.

## 12. Technology Stack

- Python
- Flask
- SQLite
- Requests HTTP library
- Docker and Docker Compose

---

**Project:** Bazar Distributed Online Bookstore  
**Component:** Order Service  
**API Version:** 1.0
