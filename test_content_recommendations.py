#!/usr/bin/env python3
"""
Test script to verify content recommendations are working correctly.
"""

import sys
import os

from uuid import uuid4
from datetime import datetime
from sqlmodel import Session, select

from backend.data.database import engine
from backend.data.models.resource import ContentResource
from backend.data.models.client import Client
from backend.data.models.user import User
from backend.agent_core.content_resource_service import get_content_recommendations_for_user

def test_content_recommendations():
    """Test that content recommendations are working correctly."""
    
    with Session(engine) as session:
        # Get the therapy user
        user = session.exec(select(User).where(User.email == 'sarah.chen@therapypractice.com')).first()
        
        if not user:
            print("❌ Therapy user not found")
            return
        
        print(f"✅ Found therapy user: {user.email}")
        
        # Get all clients for this user
        clients = session.exec(select(Client).where(Client.user_id == user.id)).all()
        print(f"✅ Found {len(clients)} clients:")
        for client in clients:
            print(f"  - {client.full_name}: user_tags={client.user_tags}, ai_tags={client.ai_tags}")
        
        # Get all content resources for this user
        resources = session.exec(select(ContentResource).where(ContentResource.user_id == user.id)).all()
        print(f"✅ Found {len(resources)} content resources:")
        for resource in resources:
            print(f"  - {resource.title}: categories={resource.categories}, status={resource.status}")
        
        # Test content recommendations
        print(f"\n🔍 Testing content recommendations for user: {user.email}")
        recommendations = get_content_recommendations_for_user(user.id)
        
        print(f"✅ Found {len(recommendations)} content recommendations:")
        for rec in recommendations:
            print(f"  - Resource: {rec['resource']['title']}")
            print(f"    Categories: {rec['resource']['categories']}")
            print(f"    Matched clients: {len(rec['matched_clients'])}")
            for client in rec['matched_clients']:
                print(f"      * {client['client_name']} (ID: {client['client_id']})")
                print(f"        Match reason: {client['match_reason']}")
            print(f"    Generated message: {rec['generated_message'][:100]}...")
            print()
        
        # Test the specific anxiety meditation match
        anxiety_resource = session.exec(
            select(ContentResource).where(ContentResource.title == 'Anxiety Meditation')
        ).first()
        
        if anxiety_resource:
            print(f"🔍 Testing specific match: Anxiety Meditation")
            print(f"  Resource categories: {anxiety_resource.categories}")
            
            jennifer = session.exec(
                select(Client).where(Client.full_name == 'Jennifer Martinez')
            ).first()
            
            if jennifer:
                print(f"  Jennifer Martinez tags: {jennifer.user_tags}")
                
                # Check if they should match
                resource_categories = set(anxiety_resource.categories or [])
                jennifer_tags = set(jennifer.user_tags or [])
                
                overlap = resource_categories.intersection(jennifer_tags)
                print(f"  Overlap: {overlap}")
                
                if overlap:
                    print("✅ MATCH FOUND: Jennifer Martinez should see Anxiety Meditation")
                else:
                    print("❌ NO MATCH: Jennifer Martinez should not see Anxiety Meditation")
            else:
                print("❌ Jennifer Martinez not found")
        else:
            print("❌ Anxiety Meditation resource not found")

if __name__ == "__main__":
    test_content_recommendations() 