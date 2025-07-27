#!/usr/bin/env python3
"""
Test script to measure manual contact addition performance.
Run this to verify that the optimizations are working.
"""

import asyncio
import time
import uuid
from datetime import datetime
from data.database import engine
from data.models.client import ClientCreate
from data import crm as crm_service

async def test_manual_contact_performance():
    """Test the performance of manual contact addition."""
    
    # Test user ID (replace with an actual user ID from your database)
    test_user_id = uuid.uuid4()  # You'll need to replace this with a real user ID
    
    # Test client data
    test_client_data = ClientCreate(
        full_name="Performance Test Contact",
        email="performance@test.com",
        phone="555-123-4567"
    )
    
    print(f"Testing manual contact addition performance...")
    print(f"User ID: {test_user_id}")
    print(f"Client: {test_client_data.full_name}")
    
    # Measure the time
    start_time = time.time()
    
    try:
        # Create the client
        client, is_new = await crm_service.create_or_update_client(
            user_id=test_user_id,
            client_data=test_client_data
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Contact creation completed in {duration:.2f} seconds")
        print(f"Client ID: {client.id}")
        print(f"Is new: {is_new}")
        
        if duration < 5.0:
            print("✅ Performance is good (< 5 seconds)")
        elif duration < 10.0:
            print("⚠️  Performance is acceptable (5-10 seconds)")
        else:
            print("❌ Performance is poor (> 10 seconds)")
            
    except Exception as e:
        print(f"❌ Error during contact creation: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_manual_contact_performance()) 