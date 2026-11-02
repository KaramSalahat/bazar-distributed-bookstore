# Frontend Service API Documentation

## 1. Overview

The Frontend Service is the entry point for clients interacting with the Bazar Distributed Online Bookstore.

It is implemented using Python and Flask and communicates with two independent backend microservices:

- **Catalog Service:** Handles book searches and book information.
- **Order Service:** Handles purchase requests and order processing.

The Frontend Service forwards client requests to the appropriate backend service and returns the backend's JSON response and HTTP status code.

**Service Port:** `5000`

**Base URL:** `http://localhost:5000`

## 2. API Endpoints

### 2.1 Health Check

**Endpoint:** `GET /health`

Checks whether the Frontend Service is running.

**Successful Response — HTTP 200**

```json
{
  "service": "frontend",
  "status": "ok"
}
```

**Example:**

```bash
curl -i http://localhost:5000/health
```

### 2.2 Search Books

**Endpoint:** `GET /search/<topic>`

Searches for books belonging to a specified topic.

The Frontend Service forwards the request to the Catalog Service using:

`GET /search?topic=<topic>`

**Example Request:**

```bash
curl -i "http://localhost:5000/search/distributed%20systems"
```

**Successful Response — HTTP 200**

```json
{
  "books": [
    {
      "id": 1,
      "title": "How to get a good grade in DOS in 40 minutes a day.",
      "topic": "distributed systems",
      "price": 50.0,
      "stock": 5
    },
    {
      "id": 2,
      "title": "RPCs for Noobs.",
      "topic": "distributed systems",
      "price": 45.0,
      "stock": 8
    }
  ],
  "count": 2,
  "topic": "distributed systems"
}
```

**Note:** Stock values are examples from the tested environment and may change after purchases.

**Additional Example:**

```bash
curl -i "http://localhost:5000/search/undergraduate%20school"
```

This request searches for books in the `undergraduate school` category.

### 2.3 Get Book Information

**Endpoint:** `GET /info/<item_number>`

Retrieves information about a specific book using its numeric identifier.

The request is forwarded to:

`GET /info/<item_number>` on the Catalog Service.

**Example Request:**

```bash
curl -i http://localhost:5000/info/1
```

**Successful Response — HTTP 200**

```json
{
  "id": 1,
  "title": "How to get a good grade in DOS in 40 minutes a day.",
  "topic": "distributed systems",
  "price": 50.0,
  "stock": 5
}
```

**Book Not Found — HTTP 404**

The Frontend Service forwards the Catalog Service's HTTP 404 response and JSON body.

### 2.4 Purchase a Book

**Endpoint:** `POST /purchase`

**Content-Type:** `application/json`

Accepts a purchase request and forwards it to the Order Service.

**Example Request:**

```bash
curl -i -X POST http://localhost:5000/purchase \
  -H "Content-Type: application/json" \
  -d '{"item_number":1,"quantity":1,"request_id":"frontend-example-001"}'
```

**Request Body:**

```json
{
  "item_number": 1,
  "quantity": 1,
  "request_id": "frontend-example-001"
}
```

| Field | Type | Description |
|---|---|---|
| `item_number` | Integer | Identifier of the book being purchased |
| `quantity` | Integer | Number of copies; defaults to 1 in the Order Service |
| `request_id` | String | Unique identifier used to prevent duplicate processing |

The Frontend Service validates that the request body is a JSON object. Detailed purchase validation is performed by the Order Service.

**Successful Purchase — HTTP 201**

```json
{
  "message": "Purchase completed successfully",
  "order": {
    "...": "Saved order details"
  }
}
```

The exact order fields are determined by the Order Service database implementation.

**Important:** Executing this example creates an order and may reduce book stock.

## 3. Error Handling

The Frontend Service handles communication failures and invalid backend responses.

| HTTP Status | Condition |
|---|---|
| `400` | Purchase request body is not a JSON object |
| `502` | Invalid JSON response from Catalog or Order Service |
| `503` | Backend service unavailable or HTTP request timed out |

### Catalog Service Unavailable — HTTP 503

```json
{
  "error": "Catalog service unavailable"
}
```

### Invalid Catalog Response — HTTP 502

```json
{
  "error": "Invalid catalog response"
}
```

### Order Service Unavailable — HTTP 503

```json
{
  "error": "Order service unavailable or timed out"
}
```

### Invalid Order Service Response — HTTP 502

```json
{
  "error": "Invalid order service response"
}
```

The Frontend Service also forwards other HTTP status codes returned by the backend services, including purchase-related errors such as HTTP 404 and HTTP 409.

## 4. Inter-Service Communication

The Frontend Service uses the Python `requests` library for synchronous HTTP communication.

### Catalog Service

**Environment Variable:** `CATALOG_SERVICE_URL`

**Default:** `http://127.0.0.1:5001`

Used for:

- Searching books.
- Retrieving book details.

**HTTP Timeout:** 5 seconds.

### Order Service

**Environment Variable:** `ORDER_SERVICE_URL`

**Default:** `http://127.0.0.1:5002`

Used for:

- Forwarding purchase requests.

**HTTP Timeout:** 15 seconds.

In Docker Compose, service addresses are configured using environment variables so that containers can communicate over the Docker network.

## 5. System Request Flow

### Search Request

Client → Frontend Service → Catalog Service → Frontend Service → Client

### Book Information Request

Client → Frontend Service → Catalog Service → Frontend Service → Client

### Purchase Request

Client → Frontend Service → Order Service → Catalog Service

The Catalog Service provides book information and performs the stock deduction.

The purchase result then travels back through the Order Service and Frontend Service to the client.

## 6. Service Responsibilities

The Frontend Service is responsible for:

1. Receiving client HTTP requests.
2. Routing requests to the appropriate backend microservice.
3. Forwarding JSON request bodies for purchases.
4. Returning backend JSON responses and HTTP status codes.
5. Handling network failures and invalid JSON responses.

The Frontend Service does not directly access the Catalog or Order SQLite databases.

## 7. Testing

The following commands can be used to verify the Frontend Service.

**Health Check:**

```bash
curl -i http://localhost:5000/health
```

**Search Distributed Systems Books:**

```bash
curl -i "http://localhost:5000/search/distributed%20systems"
```

**Search Undergraduate School Books:**

```bash
curl -i "http://localhost:5000/search/undergraduate%20school"
```

**Retrieve Book Information:**

```bash
curl -i http://localhost:5000/info/1
```

**Retrieve a Nonexistent Book:**

```bash
curl -i http://localhost:5000/info/9999
```

Purchase functionality is tested separately using unique request identifiers.

## 8. Technology Stack

- Python 3
- Flask
- Requests HTTP library
- Docker
- Docker Compose
- REST APIs
- JSON

## 9. Architecture Notes

The Frontend Service acts as an HTTP gateway rather than a graphical user interface.

It separates client-facing API endpoints from backend business logic.

The Catalog Service manages book information and inventory, while the Order Service manages purchases and order records.

This separation allows the three services to be developed, tested, and deployed as independent components.

---

**Project:** Bazar Distributed Online Bookstore  
**Component:** Frontend Service  
**API Version:** 1.0
