"""
Test script for database connection.
"""

import asyncio
import asyncpg

async def test_location_endpoint():
    """Test database connection and query."""
    try:
        conn = await asyncpg.connect('postgresql://postgres:root205@localhost:5432/transport_tracking')

        result = await conn.fetchrow("""
            SELECT b.bus_number, r.route_name, bl.latitude, bl.longitude
            FROM transport.buses b
            LEFT JOIN transport.bus_routes br ON b.bus_id = br.bus_id AND br.is_current = true
            LEFT JOIN transport.routes r ON br.route_id = r.route_id
            LEFT JOIN transport.bus_locations bl ON b.bus_id = bl.bus_id
            WHERE b.bus_id = 1
            ORDER BY bl.recorded_at DESC
            LIMIT 1
        """)

        if result:
            route_name = result['route_name'] or 'None'
            print(f'✅ Test data available: Bus {result["bus_number"]} on route {route_name}')
        else:
            print('⚠️  No test data found')

        await conn.close()
        print('✅ Database test completed successfully')

    except Exception as e:
        print(f'❌ Database test failed: {e}')

if __name__ == "__main__":
    asyncio.run(test_location_endpoint())
