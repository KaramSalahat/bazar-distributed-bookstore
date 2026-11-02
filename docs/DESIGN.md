
# Bazar.com – A Multi-tier Online Book Store
## System Design Document

**Course:** Distributed and Operating Systems
**Semester:** Fall 2026
**Project:** Lab 1 – Bazar.com

## 1. Introduction

Bazar.com is a distributed online bookstore implemented using Python, Flask, SQLite, Docker, and Docker Compose. The system supports searching for books by topic, retrieving book information, and purchasing available books. Its purpose is to demonstrate REST-based communication between independent services, persistent storage, and concurrent inventory management.

## 2. System Architecture

The application consists of three independent services, each running in a separate Docker container.

**Frontend Service (Port 5000):** Acts as the client-facing entry point. It receives search, information, and purchase requests, forwards them to the appropriate backend service, and returns JSON responses. It does not directly access backend databases.

**Catalog Service (Port 5001):** Maintains book titles, topics, prices, and available stock in `books.db` (SQLite). It supports searching, retrieving book details, updating prices, increasing stock, and decreasing stock. Its main endpoints are:

- `GET /search?topic=...`
- `GET /info/<id>`
- `PATCH /books/<id>/price`
- `PATCH /books/<id>/increment`
- `PATCH /books/<id>/decrement`

**Order Service (Port 5002):** Processes purchase requests, verifies book availability through the Catalog Service, requests stock reduction, and records orders in `orders.db` (SQLite). Each purchase includes an item number, quantity, and unique request identifier. A successful purchase produces the log message `bought book book_name`.

### Communication Architecture

The services exchange JSON messages through synchronous HTTP REST requests.

Search and information requests follow:

Client → Frontend → Catalog → Frontend → Client

Purchase requests follow:

Client → Frontend → Order → Catalog → Order → Frontend → Client

Docker Compose provides networking between containers using service names and internal ports.

## 3. Main Operations

**Search:** The client sends a topic to the Frontend Service, which forwards it to the Catalog Service. The Catalog Service searches its SQLite database and returns matching books as JSON.

**Book Information:** The Frontend requests information about a specific book from the Catalog Service, which returns its identifier, title, topic, price, and stock.

**Purchase:** The client submits a purchase request through the Frontend Service. The Order Service validates the request, creates an order record, retrieves book information, and checks availability. It then requests an atomic stock decrement from the Catalog Service. If successful, the order is marked completed and the required purchase message is printed. Invalid books and insufficient stock produce appropriate error responses.

## 4. Persistence and Concurrency

The Catalog and Order services maintain separate SQLite databases. Book information and inventory are stored in `books.db`, while order identifiers, quantities, prices, timestamps, and statuses are stored in `orders.db`.

Docker Compose bind mounts preserve these databases across container recreation.

To prevent overselling, the Catalog Service performs stock reduction using an atomic conditional SQLite UPDATE. The update succeeds only when enough stock is available, preventing negative inventory under concurrent requests.

The Order Service uses unique `request_id` values to reduce duplicate processing. Repeating an already completed request with the same identifier and purchase data does not deduct stock again. Reusing the identifier with different purchase data is rejected.

Order statuses include pending, processing, completed, failed, and uncertain.

## 5. Design Decisions and Trade-offs

**Microservices:** Separate services improve modularity and clarify responsibilities, but introduce network communication and distributed failure scenarios.

**REST and JSON:** These technologies simplify integration and testing, although synchronous calls depend on backend availability.

**SQLite:** Provides lightweight persistent storage and transactional updates without requiring a separate database server. However, it has limited write scalability compared with larger database systems.

**Docker Compose:** Simplifies deployment and service networking. The three containers are logically separated, although they may run on one physical computer.

**Request identifiers:** Reduce duplicate order processing, but do not provide a distributed transaction across services.

## 6. Error Handling and Known Limitations

The system validates input and returns HTTP errors for missing books, invalid quantities, insufficient stock, and unavailable services.

Important limitations include:

- Stock decrement and order completion are not one atomic cross-service transaction.
- A timeout after stock deduction may leave an order in an uncertain state.
- The Catalog Service does not independently support idempotent stock updates.
- The increment endpoint allows stock adjustments but does not automatically compensate failed purchases.
- SQLite and single-host Docker Compose are suitable for the lab but have production scalability and deployment limitations.

Possible improvements include distributed transaction compensation, Catalog-level idempotency, automated recovery of uncertain orders, PostgreSQL, authentication, and deployment across separate machines.

## 7. Running and Testing

From the project root directory, start the three services:

```bash
docker compose up --build -d
```

Check container status:

```bash
docker compose ps
```

Test service health:

```bash
curl http://localhost:5000/health
curl http://localhost:5001/health
curl http://localhost:5002/health
```

Search for books:

```bash
curl http://localhost:5000/search/distributed%20systems
```

Retrieve book information:

```bash
curl http://localhost:5000/info/1
```

Submit a purchase (this changes stock when successful):

```bash
curl -X POST http://localhost:5000/purchase \
  -H "Content-Type: application/json" \
  -d '{"item_number":1,"quantity":1,"request_id":"unique-demo-request"}'
```

Inspect purchase logs:

```bash
docker compose logs order | grep "bought book"
```

Stop the application:

```bash
docker compose down
```

For detailed request formats, responses, and error codes, see `CATALOG_API.md`, `ORDER_API.md`, and `FRONTEND_API.md`.

## 8. Conclusion

Bazar.com demonstrates a three-service distributed bookstore with REST communication, persistent SQLite storage, book searching, information retrieval, purchase processing, and concurrency-safe stock reduction. It also illustrates the challenges of duplicate requests, partial failures, and consistency between distributed services.
