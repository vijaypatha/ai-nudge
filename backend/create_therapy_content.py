#!/usr/bin/env python3
"""
Script to create content resources for the therapy user.
"""

import sys
import os

from uuid import uuid4
from datetime import datetime
from sqlmodel import Session, select

from data.database import engine
from data.models.resource import ContentResource
from data.models.user import User

def create_therapy_content():
    """Create content resources for the therapy user."""
    
    with Session(engine) as session:
        # Get the therapy user
        therapy_user = session.exec(
            select(User).where(User.email == "sarah.chen@therapypractice.com")
        ).first()
        
        if not therapy_user:
            print("❌ Therapy user not found")
            return
        
        print(f"✅ Found therapy user: {therapy_user.email}")
        
        # Create Anxiety Meditation resource
        anxiety_resource = session.exec(
            select(ContentResource).where(ContentResource.title == "Anxiety Meditation")
        ).first()
        
        if not anxiety_resource:
            anxiety_resource = ContentResource(
                id=uuid4(),
                user_id=therapy_user.id,
                title="Anxiety Meditation",
                description="Mindful Breathing for Anxiety",
                url="https://example.com/anxiety-meditation",
                categories=["anxiety", "meditation", "mindfulness"],
                content_type="video",
                status="active",
                usage_count=0,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(anxiety_resource)
            session.commit()
            session.refresh(anxiety_resource)
            print(f"✅ Created Anxiety Meditation resource")
        else:
            print(f"✅ Anxiety Meditation resource already exists")
        
        # Create additional therapy resources
        therapy_resources = [
            {
                "title": "Stress Management Guide",
                "description": "Practical techniques for managing daily stress",
                "url": "https://example.com/stress-management",
                "categories": ["stress", "coping", "wellness"],
                "content_type": "document"
            },
            {
                "title": "Grief Support Resources",
                "description": "Supporting clients through loss and grief",
                "url": "https://example.com/grief-support",
                "categories": ["grief", "loss", "support"],
                "content_type": "document"
            },
            {
                "title": "Parenting Tips for Stress",
                "description": "Managing stress while parenting",
                "url": "https://example.com/parenting-stress",
                "categories": ["parenting", "stress", "family"],
                "content_type": "article"
            }
        ]
        
        for resource_data in therapy_resources:
            existing = session.exec(
                select(ContentResource).where(ContentResource.title == resource_data["title"])
            ).first()
            
            if not existing:
                resource = ContentResource(
                    id=uuid4(),
                    user_id=therapy_user.id,
                    title=resource_data["title"],
                    description=resource_data["description"],
                    url=resource_data["url"],
                    categories=resource_data["categories"],
                    content_type=resource_data["content_type"],
                    status="active",
                    usage_count=0,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                session.add(resource)
                print(f"✅ Created {resource_data['title']} resource")
        
        session.commit()
        
        # Verify all resources were created
        resources = session.exec(
            select(ContentResource).where(ContentResource.user_id == therapy_user.id)
        ).all()
        
        print(f"\n✅ Created {len(resources)} content resources for therapy user:")
        for resource in resources:
            print(f"  - {resource.title}: {resource.categories}")
        
        print(f"\n🎯 Now test the content recommendations to see matches!")

if __name__ == "__main__":
    create_therapy_content() 