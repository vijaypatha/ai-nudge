#!/usr/bin/env python3
"""
Simple test script to run the pipeline and create market events.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from workflow.pipeline import run_main_opportunity_pipeline
from data.database import get_session
from data.models.event import MarketEvent
from sqlmodel import select

async def main():
    print("🧪 Testing pipeline...")
    
    # Run the pipeline
    await run_main_opportunity_pipeline()
    
    # Check if events were created
    with next(get_session()) as session:
        events = session.exec(select(MarketEvent)).all()
        print(f"📊 Found {len(events)} market events in database")
        
        for event in events:
            print(f"  - {event.event_type}: {event.entity_id}")
    
    print("✅ Test complete!")

if __name__ == "__main__":
    asyncio.run(main()) 