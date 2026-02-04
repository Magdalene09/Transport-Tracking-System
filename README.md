# TransportTrackingSystem

A backend-focused **Public Transport Tracking API** that tracks buses in real time, stores GPS location history, associates buses with routes and ordered stops, and provides **live tracking** and **ETA (Estimated Time of Arrival)** calculations.

The project is designed as a realistic **backend systems project**, combining async APIs, geospatial calculations, caching, database modeling, and a lightweight frontend dashboard.

---

## 📌 Project Overview

This system allows you to:

* Track where a bus is *right now*
* View its historical GPS locations
* Associate buses with routes and ordered stops
* Calculate ETAs using recent movement data
* Query route assignments and stop details

---

## 🧰 Tech Stack

* **Backend API:** FastAPI
* **Database:** PostgreSQL (custom `transport` schema)
* **Caching:** In-memory cache with TTL
* **Frontend:** Static HTML/CSS/JavaScript dashboard
* **Tests:** pytest-based API tests

---

## 🚀 Features & API Capabilities

### 1️⃣ Health & Monitoring

* `GET /health`

  * Checks if the API is running

* `GET /health/detailed`

  * Returns cache statistics and component status

---

### 2️⃣ Live Bus Tracking

* `GET /bus/{bus_id}/live`

  * Bus metadata (bus number, active/inactive)
  * Latest GPS location (latitude, longitude, timestamp)
  * Current assigned route (if any)

---

### 3️⃣ Bus Location History

* `GET /bus/{bus_id}/history?limit=50`

  * Returns the most recent GPS samples for the bus
  * Ordered from newest → oldest

---

### 4️⃣ Active Buses

* `GET /bus/active`

  * Lists all active buses
  * Includes latest location and current route (if assigned)

---

### 5️⃣ Route Assignment & Lookup

* `GET /bus/{bus_number}/routes`

  * Current route ID
  * Previous route ID (most recent non-current assignment)

* `GET /bus/{bus_number}/routes/detailed`

  * Route name & number
  * Assignment timestamps
  * Ordered stop list

* `GET /bus/routes/all`

  * Returns all routes and their stops

---

### 6️⃣ ETA (Estimated Time of Arrival)

* `GET /bus/{bus_number}/eta?route_id=X`

  * Returns a human-readable ETA string
  * Includes the bus’s current route ID

* `GET /bus/{bus_number}/eta/detailed?route_id=X&stop_order=Y`

  * Returns ETA calculation details:

    * Distance
    * Average speed
    * Target stop
    * Selected calculation mode

---

## 🧮 How ETA Is Calculated (High Level)

### Bus on the Same Route

1. Fetch ordered stops for the route
2. Fetch recent GPS locations (default: last 10)
3. Compute rolling average speed using **Haversine distance**
4. Identify the nearest upcoming stop
5. Calculate ETA:

```
ETA (minutes) = (distance_km / avg_speed_kmh) × 60
(minimum 1 minute)
```

Optional: target a specific stop using `stop_order`.

---

### Bus on a Different Route (Placeholder Logic)

Instead of real map routing, a simplified heuristic is used:

```
route_difference = |requested_route_id - current_route_id|
ETA = (route_difference × 90) + extra_time
extra_time = 30 minutes per route difference (capped at 180)
```

⚠️ This is a **placeholder ETA model**, not geographically accurate.

---

## ⚡ Caching Behavior

* In-memory cache using Python dictionaries
* Default TTL: **15 seconds**
* Cached items:

  * Bus ETA responses
  * Per-stop ETA structures

A background task runs every **300 seconds** to clean expired entries.

⚠️ Cache is **not persistent** and resets on application restart.

---

## 🗄️ Database Design

All tables are under the PostgreSQL schema: `transport`

### Main Tables

* **buses**

  * `bus_id`, `bus_number` (unique), `is_active`, `created_at`

* **routes**

  * `route_id`, `route_name`, `route_number` (unique), `created_at`

* **stops**

  * Belongs to a route
  * Ordered by `stop_order`
  * Includes latitude & longitude

* **bus_locations**

  * Time-series GPS data
  * One row per recorded location

* **bus_routes**

  * Join table (bus ↔ route)
  * `is_current` marks active assignment

The `setupdb.py` script creates all tables and loads sample data.

---

### Database

* PostgreSQL
* Custom schema: `transport`

### Middleware & Runtime

* CORS Middleware
* GZip Middleware
* Background cache cleanup task

### Frontend

* HTML
* CSS
* Vanilla JavaScript

### Testing

* pytest
* pytest-asyncio / anyio
* httpx (ASGITransport)

---

## 🧪 Testing

Run automated tests with:

```bash
pytest
```

Tests validate key API endpoints using FastAPI’s ASGI test client.

---

## ⚠️ Limitations

* ETA logic for different routes is heuristic-based, not map-accurate
* No real-time GPS ingestion (data is simulated)
* In-memory cache is not shared across instances
* No authentication or authorization
