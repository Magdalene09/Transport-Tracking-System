"""
Database setup script with sample data.
"""

import asyncpg
import asyncio
import sys

async def setup_database():
    """Set up the database with schema and sample data."""
    try:
        print("🔧 Setting up database...")

        conn = await asyncpg.connect('postgresql://postgres:root205@localhost:5432/postgres')

        try:
            await conn.execute('DROP DATABASE IF EXISTS transport_tracking')
            print("🗑️  Dropped existing database")
        except:
            pass

        await conn.execute('CREATE DATABASE transport_tracking')
        print("✅ Database 'transport_tracking' created")

        await conn.close()

        conn = await asyncpg.connect('postgresql://postgres:root205@localhost:5432/transport_tracking')

        await conn.execute('CREATE SCHEMA IF NOT EXISTS transport')
        print("✅ Schema 'transport' created")

        await conn.execute("""
            CREATE TABLE transport.buses (
                bus_id SERIAL PRIMARY KEY,
                bus_number VARCHAR(20) UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT true,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE transport.routes (
                route_id SERIAL PRIMARY KEY,
                route_name VARCHAR(100) NOT NULL,
                route_number VARCHAR(20) UNIQUE NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE transport.stops (
                stop_id SERIAL PRIMARY KEY,
                route_id INTEGER NOT NULL REFERENCES transport.routes(route_id) ON DELETE CASCADE,
                stop_name VARCHAR(100) NOT NULL,
                latitude DECIMAL(10, 8) NOT NULL,
                longitude DECIMAL(11, 8) NOT NULL,
                stop_order INTEGER NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(route_id, stop_order)
            )
        """)

        await conn.execute("""
            CREATE TABLE transport.bus_locations (
                location_id SERIAL PRIMARY KEY,
                bus_id INTEGER NOT NULL REFERENCES transport.buses(bus_id) ON DELETE CASCADE,
                latitude DECIMAL(10, 8) NOT NULL,
                longitude DECIMAL(11, 8) NOT NULL,
                recorded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await conn.execute("""
            CREATE TABLE transport.bus_routes (
                bus_id INTEGER NOT NULL REFERENCES transport.buses(bus_id) ON DELETE CASCADE,
                route_id INTEGER NOT NULL REFERENCES transport.routes(route_id) ON DELETE CASCADE,
                assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                is_current BOOLEAN DEFAULT false,
                PRIMARY KEY (bus_id, route_id)
            )
        """)

        print("✅ Tables created")

        await conn.execute('CREATE INDEX idx_buses_bus_number ON transport.buses(bus_number)')
        await conn.execute('CREATE INDEX idx_routes_route_number ON transport.routes(route_number)')
        await conn.execute('CREATE INDEX idx_stops_route_id ON transport.stops(route_id)')
        await conn.execute('CREATE INDEX idx_bus_locations_bus_id_recorded_at ON transport.bus_locations(bus_id, recorded_at DESC)')
        await conn.execute('CREATE INDEX idx_bus_routes_bus_id_current ON transport.bus_routes(bus_id, is_current) WHERE is_current = true')

        print("✅ Indexes created")

        await conn.execute("""
            INSERT INTO transport.buses (bus_number, is_active) VALUES
            ('BUS-001', true), ('BUS-002', true), ('BUS-003', true),
            ('BUS-004', true), ('BUS-005', true), ('BUS-006', true),
            ('BUS-007', true), ('BUS-008', true), ('BUS-009', true),
            ('BUS-010', true), ('BUS-011', true), ('BUS-012', true),
            ('BUS-013', true), ('BUS-014', true), ('BUS-015', false)
        """)

        await conn.execute("""
            INSERT INTO transport.routes (route_name, route_number) VALUES
            ('Downtown Express', 'R1'), ('Airport Shuttle', 'R2'), ('University Loop', 'R3'),
            ('Mall Connector', 'R4'), ('Hospital Route', 'R5'), ('Stadium Special', 'R6'),
            ('Beach Line', 'R7'), ('Mountain View', 'R8'), ('River Crossing', 'R9'),
            ('Park & Ride', 'R10'), ('Central Station', 'R11'), ('North District', 'R12'),
            ('South District', 'R13'), ('East Side', 'R14'), ('West Side', 'R15')
        """)

        await conn.execute("""
            INSERT INTO transport.stops (route_id, stop_name, latitude, longitude, stop_order) VALUES
            (1, 'Central Station', 40.7128, -74.0060, 1),
            (1, 'Financial District', 40.7074, -74.0113, 2),
            (1, 'Times Square', 40.7580, -73.9855, 3),
            (1, 'Grand Central', 40.7527, -73.9772, 4),
            (1, 'Penn Station', 40.7505, -73.9934, 5),
            (2, 'Airport Terminal 1', 40.6413, -73.7781, 1),
            (2, 'Airport Terminal 2', 40.6425, -73.7800, 2),
            (2, 'Airport Parking', 40.6430, -73.7820, 3),
            (3, 'University Main Gate', 40.7295, -73.9965, 1),
            (3, 'Science Building', 40.7300, -73.9970, 2),
            (3, 'Library Stop', 40.7310, -73.9980, 3)
        """)

        await conn.execute("""
            INSERT INTO transport.bus_locations (bus_id, latitude, longitude, recorded_at) VALUES
            (1, 40.7128, -74.0060, CURRENT_TIMESTAMP - INTERVAL '1 minute'),
            (1, 40.7130, -74.0058, CURRENT_TIMESTAMP - INTERVAL '2 minutes'),
            (1, 40.7132, -74.0056, CURRENT_TIMESTAMP - INTERVAL '3 minutes'),
            (2, 40.7074, -74.0113, CURRENT_TIMESTAMP - INTERVAL '2 minutes'),
            (3, 40.7580, -73.9855, CURRENT_TIMESTAMP - INTERVAL '3 minutes'),
            (4, 40.7527, -73.9772, CURRENT_TIMESTAMP - INTERVAL '4 minutes'),
            (5, 40.7505, -73.9934, CURRENT_TIMESTAMP - INTERVAL '5 minutes'),
            (6, 40.6413, -73.7781, CURRENT_TIMESTAMP - INTERVAL '6 minutes'),
            (7, 40.6425, -73.7800, CURRENT_TIMESTAMP - INTERVAL '7 minutes'),
            (8, 40.6430, -73.7820, CURRENT_TIMESTAMP - INTERVAL '8 minutes')
        """)

        await conn.execute("""
            INSERT INTO transport.bus_routes (bus_id, route_id, assigned_at, is_current) VALUES
            (1, 1, CURRENT_TIMESTAMP - INTERVAL '2 hours', true),
            (2, 1, CURRENT_TIMESTAMP - INTERVAL '2 hours', true),
            (3, 2, CURRENT_TIMESTAMP - INTERVAL '2 hours', true),
            (4, 2, CURRENT_TIMESTAMP - INTERVAL '2 hours', true),
            (5, 3, CURRENT_TIMESTAMP - INTERVAL '2 hours', true),
            (6, 3, CURRENT_TIMESTAMP - INTERVAL '2 hours', true),
            (7, 1, CURRENT_TIMESTAMP - INTERVAL '2 hours', true),
            (8, 2, CURRENT_TIMESTAMP - INTERVAL '2 hours', true),
            (1, 2, CURRENT_TIMESTAMP - INTERVAL '24 hours', false),
            (2, 3, CURRENT_TIMESTAMP - INTERVAL '24 hours', false),
            (3, 1, CURRENT_TIMESTAMP - INTERVAL '24 hours', false)
        """)

        print("✅ Sample data loaded")

        buses = await conn.fetchval('SELECT COUNT(*) FROM transport.buses')
        routes = await conn.fetchval('SELECT COUNT(*) FROM transport.routes')
        locations = await conn.fetchval('SELECT COUNT(*) FROM transport.bus_locations')

        print(f"📊 Verification: {buses} buses, {routes} routes, {locations} location records")

        await conn.close()
        print("🎉 Database setup complete!")
        print("\n🚀 Start the server with: uvicorn main:app --reload")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(setup_database())
