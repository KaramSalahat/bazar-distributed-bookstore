
# Bazar Distributed Online Bookstore

**Distributed and Operating Systems — Lab 1**

## 1. Project Overview

Bazar is a distributed online bookstore implemented using a microservices architecture.

The system allows clients to search for books by topic, retrieve book information, and purchase books while maintaining inventory and recording orders.

The application consists of three independent Flask services communicating through REST APIs.

## 2. System Architecture

The system contains three microservices:

| Service | Port | Responsibility |
|---|---|---|
| Frontend Service | 5000 | Client-facing API gateway |
| Catalog Service | 5001 | Book information, searching, pricing, and inventory |
| Order Service | 5002 | Purchase processing, order storage, and duplicate request handling |

### Communication Flow

**Book Search**

Client → Frontend Service → Catalog Service → Frontend Service → Client

**Book Information**

Client → Frontend Service → Catalog Service → Frontend Service → Client

**Book Purchase**

Client → Frontend Service → Order Service → Catalog Service

The purchase result is returned to the client through the Order Service and Frontend Service.

Services communicate synchronously using HTTP requests and JSON responses.

## 3. Technologies Used

- Python 3
- Flask
- SQLite
- REST APIs
- JSON
- Python Requests library
- Docker
- Docker Compose
- Git and GitHub
- Ubuntu WSL

## 4. Project Structure

```text
bazar-distributed-bookstore/
├── catalog-service/
│   ├── app.py
│   ├── init_db.py
│   ├── books.json
│   ├── requirements.txt
│   └── Dockerfile
├── order-service/
│   ├── app.py
│   ├── database.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend-service/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── docs/
│   ├── CATALOG_API.md
│   ├── ORDER_API.md
│   ├── FRONTEND_API.md
│   ├── DESIGN.md
│   └── OUTPUT.txt
├── docker-compose.yml
├── .gitignore
└── README.md
```

SQLite databases are created or initialized locally and are not committed to Git.

## 5. Available Books

The bookstore contains the four book titles required for the lab.

| ID | Book Title | Topic |
|---|---|---|
| 1 | How to get a good grade in DOS in 40 minutes a day. | distributed systems |
| 2 | RPCs for Noobs. | distributed systems |
| 3 | Xen and the Art of Surviving Undergraduate School. | undergraduate school |
| 4 | Cooking for the Impatient Undergrad. | undergraduate school |

Book prices and available stock are maintained by the Catalog Service.

Inventory quantities can change after successful purchases.

## 6. Running the Project with Docker Compose

### Prerequisites

- Docker Desktop or Docker Engine
- Docker Compose
- Git

### Clone the Repository

```bash
git clone git@github.com:KaramSalahat/bazar-distributed-bookstore.git
```

### Enter the Project Directory

```bash
cd bazar-distributed-bookstore
```

### Build and Start the Services

```bash
docker compose up --build -d
```

Docker Compose starts all three services and configures their internal network communication.

### Check Service Status

```bash
docker compose ps
```

### View Service Logs

```bash
docker compose logs --tail=30
```

### Stop the Services

```bash
docker compose down
```

## 7. API Endpoints

### Frontend Service — Port 5000

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check frontend health |
| GET | `/search/<topic>` | Search books by topic |
| GET | `/info/<item_number>` | Retrieve book details |
| POST | `/purchase` | Submit a purchase request |

### Catalog Service — Port 5001

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check catalog health |
| GET | `/search?topic=<topic>` | Search books |
| GET | `/info/<item_number>` | Retrieve book information |
| PATCH | `/books/<item_number>/price` | Update book price |
| PATCH | `/books/<item_number>/decrement` | Deduct available stock |
| PATCH | `/books/<item_number>/increment` | Increase available stock |

### Order Service — Port 5002

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Check order service health |
| POST | `/purchase` | Process a purchase |

## 8. API Testing Examples

The Frontend Service provides the main entry point for client requests.

### Health Check

```bash
curl -i http://localhost:5000/health
```

### Search Distributed Systems Books

```bash
curl -i "http://localhost:5000/search/distributed%20systems"
```

### Search Undergraduate School Books

```bash
curl -i "http://localhost:5000/search/undergraduate%20school"
```

### Retrieve Book Information

```bash
curl -i http://localhost:5000/info/1
```

### Purchase a Book

```bash
curl -i -X POST http://localhost:5000/purchase \
  -H "Content-Type: application/json" \
  -d '{"item_number":1,"quantity":1,"request_id":"readme-test-001"}'
```

**Note:** A successful purchase creates an order and reduces the available stock. Use a unique `request_id` for each new purchase.

### Duplicate Purchase Request

Repeat the purchase request using the same `request_id` and purchase details.

The Order Service returns the existing completed order without deducting stock again.

### Nonexistent Book

```bash
curl -i -X POST http://localhost:5000/purchase \
  -H "Content-Type: application/json" \
  -d '{"item_number":9999,"quantity":1,"request_id":"missing-book-001"}'
```

Expected result: HTTP 404.

### Insufficient Stock

Submit a purchase quantity greater than the available stock.

Expected result: HTTP 409, without reducing the inventory.

## 9. Data Storage

### Catalog Database

The Catalog Service uses SQLite to store book information, prices, and available stock.

Initial book data is defined in `catalog-service/books.json`.

### Order Database

The Order Service uses a separate SQLite database to store orders and their processing statuses.

The services do not share a database.

Docker Compose uses local bind mounts for the Catalog and Order Service directories, allowing database files to persist across normal container restarts.

## 10. Reliability and Consistency

### Atomic Stock Deduction

The Catalog Service uses an atomic conditional database update to prevent stock quantities from becoming negative during concurrent purchase requests.

### Duplicate Request Protection

The Order Service uses a unique `request_id` to prevent duplicate purchase processing.

Repeated requests with the same identifier do not trigger another stock deduction.

### Order Status Tracking

Order records may have the following statuses:

- pending
- processing
- completed
- failed
- uncertain

### Distributed Consistency Limitation

Catalog inventory and order records are stored in separate SQLite databases.

The system does not implement a distributed transaction across the two services.

If a stock deduction succeeds but order finalization fails, manual reconciliation may be required.

## 11. Testing Summary

The project has been tested using Docker Compose and HTTP requests.

Verified scenarios include:

- All three Docker containers running.
- Frontend health check.
- Book search by topic.
- Book information retrieval.
- Successful purchase.
- Inventory reduction after purchase.
- Duplicate purchase handling.
- Rejection of nonexistent books.
- Rejection of purchases with insufficient stock.
- Inventory preservation after rejected purchases.
- Inter-service HTTP communication.
- Docker service logs.
- Updated catalog containing the four required book titles.
- Concurrent purchase requests.
- Prevention of overselling during concurrent purchases.
- Verification that inventory does not become negative.

### Concurrency Test Results

A concurrency test was performed using book ID 2, "RPCs for Noobs."

Initial available stock: **8 copies**.

Ten purchase requests were submitted concurrently using `xargs -P 10`, with a unique request ID for each request.

| Result | Number of Requests |
|---|---|
| Total concurrent requests | 10 |
| Successful purchases (HTTP 201) | 8 |
| Rejected purchases (HTTP 409) | 2 |
| Final available stock | 0 |

The results demonstrate that the system prevented overselling in this test. The Catalog Service accepted only the available quantity and rejected additional purchase requests.

Detailed execution output is available in `docs/OUTPUT.txt`.

## 12. Project Documentation

Detailed documentation is available in the `docs` directory:

- [Catalog Service API](docs/CATALOG_API.md)
- [Order Service API](docs/ORDER_API.md)
- [Frontend Service API](docs/FRONTEND_API.md)
- [System Design Document](docs/DESIGN.md)
- [Program Execution Output](docs/OUTPUT.txt)

The system design document describes the architecture, service responsibilities, communication, reliability mechanisms, limitations, and potential improvements.

The program execution output includes actual results from search, book information, purchase, duplicate request handling, and concurrent purchase testing.

## 13. Repository

**GitHub:** https://github.com/KaramSalahat/bazar-distributed-bookstore

**Default Branch:** `main`

---

**Course:** Distributed and Operating Systems  
**Assignment:** Lab 1 — Distributed Online Bookstore  
**Project:** Bazar Distributed Online Bookstore
