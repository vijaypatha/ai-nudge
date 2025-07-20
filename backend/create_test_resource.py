#!/usr/bin/env python3
"""
Script to create a test content resource and client that will generate a match.
This demonstrates the content recommendation system integrated into AI suggestions.
"""

import sys
import os

from uuid import uuid4
from datetime import datetime
from sqlmodel import Session, select

from data.database import engine
from data.models.resource import ContentResource
from data.models.client import Client
from data.models.user import User

def create_test_data():
    """Create test content resource and client that will match."""
    
    with Session(engine) as session:
        # First, get or create a test user
        test_user = session.exec(
            select(User).where(User.email == "test@example.com")
        ).first()
        
        if not test_user:
            test_user = User(
                id=uuid4(),
                email="test@example.com",
                full_name="Test User",
                phone_number="+1234567890",
                vertical="real_estate",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(test_user)
            session.commit()
            session.refresh(test_user)
            print(f"Created test user: {test_user.email}")
        
        # Create test client Jennifer
        jennifer_client = session.exec(
            select(Client).where(Client.full_name == "Jennifer Smith")
        ).first()
        
        if not jennifer_client:
            jennifer_client = Client(
                id=uuid4(),
                user_id=test_user.id,
                full_name="Jennifer Smith",
                email="jennifer@example.com",
                phone="+1234567890",
                user_tags=["first-time-buyer", "condo", "downtown"],
                ai_tags=["budget-conscious", "urban-living", "investment-minded"],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(jennifer_client)
            session.commit()
            session.refresh(jennifer_client)
            print(f"Created test client: {jennifer_client.full_name}")
            print(f"Client tags: {jennifer_client.user_tags}")
            print(f"AI tags: {jennifer_client.ai_tags}")
        
        # Create test content resource that will match Jennifer
        test_resource = session.exec(
            select(ContentResource).where(ContentResource.title == "First-Time Buyer's Guide to Downtown Condos")
        ).first()
        
        if not test_resource:
            test_resource = ContentResource(
                id=uuid4(),
                user_id=test_user.id,
                title="First-Time Buyer's Guide to Downtown Condos",
                description="Comprehensive guide for first-time buyers looking at downtown condos, including financing tips and neighborhood insights.",
                url="https://example.com/first-time-buyer-guide",
                categories=["first-time-buyer", "condo", "downtown", "financing"],
                content_type="document",
                status="active",
                usage_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(test_resource)
            session.commit()
            session.refresh(test_resource)
            print(f"Created test resource: {test_resource.title}")
            print(f"Resource categories: {test_resource.categories}")
        
        # Test the matching logic
        from agent_core.content_resource_service import find_matching_clients
        
        matched_clients = find_matching_clients(test_resource, [jennifer_client])
        
        if matched_clients:
            print(f"\n✅ SUCCESS: Resource matches {len(matched_clients)} client(s):")
            for client in matched_clients:
                print(f"  - {client.full_name}")
                print(f"    Client tags: {client.user_tags}")
                print(f"    AI tags: {client.ai_tags}")
                print(f"    Resource categories: {test_resource.categories}")
        else:
            print("\n❌ No matches found")
        
        print(f"\nTest data created successfully!")
        print(f"User ID: {test_user.id}")
        print(f"Client ID: {jennifer_client.id}")
        print(f"Resource ID: {test_resource.id}")

if __name__ == "__main__":
    create_test_data() 