# Bazar.com - Catalog Service API

## Overview

The Catalog Service manages book information, prices, and stock.

Local base URL: http://127.0.0.1:5001

Data storage: SQLite (catalog-service/books.db)

All responses use JSON.

## 1. Health Check

GET /health

Success: HTTP 200

Response:
{"service":"catalog","status":"ok"}

## 2. Search Books

GET /search?topic=distributed%20systems

Success: HTTP 200

Response contains:
- topic
- count
- books (array of matching books)

The search is case-insensitive and matches the topic field.

Errors:
- 400: Topic is required

## 3. Get Book Information

GET /info/1

Success: HTTP 200

Response fields:
- id
- title
- topic
- price
- stock

Errors:
- 404: Book not found

## 4. Update Book Price

PATCH /books/1/price

Content-Type: application/json

Request:
{"price":55}

Success: HTTP 200

Response:
{"message":"Price updated successfully","id":1,"price":55}

Errors:
- 400: JSON body is required
- 400: Price must be a non-negative finite number
- 404: Book not found

## 5. Decrement Book Stock

PATCH /books/1/decrement

Content-Type: application/json

Request:
{"quantity":2}

Success: HTTP 200

Response example:
{"message":"Stock decremented successfully","id":1,"quantity":2,"stock":8}

Errors:
- 400: JSON body is required
- 400: Quantity must be a positive integer
- 404: Book not found
- 409: Insufficient stock

An insufficient-stock response includes available_stock.

The stock decrement uses an atomic conditional SQLite UPDATE
to prevent stock from becoming negative under concurrent requests.

## 6. Increment Book Stock

PATCH /books/1/increment

Content-Type: application/json

Request:
{"quantity":1}

Success: HTTP 200

Response example:
{"message":"Stock incremented successfully","id":1,"quantity":1,"stock":6}

Errors:
- 400: JSON body is required
- 400: Quantity must be a positive integer
- 404: Book not found

The increment operation increases the available stock
of an existing book.

The quantity must be a positive integer.

The operation uses a SQLite UPDATE statement to increase
stock atomically.

This endpoint supports inventory replenishment and
manual stock adjustments.

It is not automatically invoked to compensate for
failed or uncertain orders.

## Order Service Integration Notes

The Order Service should:

1. Obtain the requested book information using GET /info/<id>.
2. Validate the requested purchase quantity.
3. Request stock decrement using PATCH /books/<id>/decrement.
4. Handle HTTP 200, 400, 404, and 409 appropriately.
5. Record successful orders in its own persistent storage.
6. Print "bought book book_name" after successful order completion.

Important:
- Checking stock with GET /info does not reserve stock.
- The decrement response determines whether stock was actually obtained.
- The Catalog API currently has no idempotency key.
- Repeating a successful decrement request can deduct stock again.
- The Order Service uses request_id to prevent duplicate
  purchase processing at the order level.
- The Catalog Service supports stock increases through
  PATCH /books/<id>/increment.
- Stock restoration is not automatically coordinated
  with failed or uncertain orders.
- Order recording and Catalog stock updates are not one
  cross-service database transaction.

## Deployment Note

127.0.0.1:5001 is for local testing.

When running in Docker Compose, the Order Service must use
the Catalog Service's Compose hostname and internal port,
rather than its own localhost address.
