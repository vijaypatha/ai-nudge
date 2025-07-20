# backend/agent_core/content_resource_service.py
# Content resource service for integrating content recommendations into AI suggestions

import logging
from typing import List, Dict, Any
from uuid import UUID
from sqlmodel import Session, select

from data.models.resource import ContentResource
from data.models.client import Client
from data.database import engine
from agent_core.llm_client import get_chat_completion

def get_content_recommendations_for_user(user_id: UUID) -> List[Dict[str, Any]]:
    """
    Get content recommendations for a user as part of the AI suggestions system.
    This integrates content resources into the Perceive layer that feeds into AI reasoning.
    """
    try:
        with Session(engine) as session:
            # Get all active content resources for the user
            resources = session.exec(
                select(ContentResource)
                .where(ContentResource.user_id == user_id)
                .where(ContentResource.status == 'active')
            ).all()
            
            if not resources:
                return []
            
            # Get all clients for the user
            clients = session.exec(
                select(Client)
                .where(Client.user_id == user_id)
            ).all()
            
            recommendations = []
            
            for resource in resources:
                # Find matching clients based on resource categories and client tags
                matched_clients = find_matching_clients(resource, clients)
                
                if matched_clients:
                    # Generate personalized message for each matched client
                    for client in matched_clients:
                        message = generate_resource_message_sync(resource, client)
                        
                        recommendation = {
                            'resource': {
                                'id': resource.id,
                                'title': resource.title,
                                'description': resource.description,
                                'url': resource.url,
                                'categories': resource.categories,
                                'content_type': resource.content_type,
                                'created_at': resource.created_at,
                                'updated_at': resource.updated_at
                            },
                            'matched_clients': [{
                                'client_id': client.id,
                                'client_name': client.full_name,
                                'match_reason': f"Matches categories: {', '.join(resource.categories)}"
                            }],
                            'generated_message': message
                        }
                        recommendations.append(recommendation)
            
            return recommendations
            
    except Exception as e:
        logging.error(f"Error getting content recommendations for user {user_id}: {e}", exc_info=True)
        return []

def find_matching_clients(resource: ContentResource, clients: List[Client]) -> List[Client]:
    """
    Find clients that match the content resource based on categories and tags.
    """
    matched_clients = []
    
    for client in clients:
        # Check if client tags match resource categories
        client_tags = set(client.user_tags or [])
        client_ai_tags = set(client.ai_tags or [])
        resource_categories = set(resource.categories or [])
        
        # Check for any overlap between client tags and resource categories
        if client_tags.intersection(resource_categories) or client_ai_tags.intersection(resource_categories):
            matched_clients.append(client)
    
    return matched_clients

def generate_resource_message_sync(resource: ContentResource, client: Client) -> str:
    """
    Generate a personalized message for sharing content with a client (synchronous version).
    """
    try:
        # Create a simple personalized message without LLM for now
        client_name = client.full_name.split()[0] if client.full_name else "there"
        
        if resource.content_type == "video":
            base_message = f"I found a helpful video about {', '.join(resource.categories or [])} that might be useful."
        elif resource.content_type == "document":
            base_message = f"I have a helpful guide about {', '.join(resource.categories or [])} that includes practical strategies."
        else:  # article or default
            base_message = f"I found a helpful article about {', '.join(resource.categories or [])} that might be useful."
        
        if resource.description:
            base_message += f" {resource.description}"
        
        base_message += f"\n\nHere's the link: {resource.url}"
        base_message += "\n\nLet me know if you find it helpful!"
        
        return f"Hi {client_name}, {base_message}"
        
    except Exception as e:
        logging.error(f"Error generating resource message: {e}", exc_info=True)
        # Fallback message
        return f"Hi {client.full_name}, I thought you might find this {resource.content_type} helpful: {resource.url}"

async def generate_resource_message(resource: ContentResource, client: Client) -> str:
    """
    Generate a personalized message for sharing content with a client (async version with LLM).
    """
    try:
        prompt = f"""
        Generate a personalized message to share content with a client.
        
        Content Resource:
        - Title: {resource.title}
        - Description: {resource.description}
        - URL: {resource.url}
        - Categories: {', '.join(resource.categories or [])}
        - Content Type: {resource.content_type}
        
        Client:
        - Name: {client.full_name}
        - Tags: {', '.join(client.user_tags or [])}
        - AI Tags: {', '.join(client.ai_tags or [])}
        
        Generate a friendly, personalized message that:
        1. Mentions the client by name
        2. Explains why this content is relevant to them
        3. Includes the content URL
        4. Encourages engagement
        5. Keeps it conversational and not too salesy
        
        Format the message for SMS (under 160 characters if possible).
        """
        
        response = await get_chat_completion(prompt)
        return response.strip() if response else f"Hi {client.full_name}, I thought you might find this {resource.content_type} helpful: {resource.url}"
        
    except Exception as e:
        logging.error(f"Error generating resource message: {e}", exc_info=True)
        # Fallback message
        return f"Hi {client.full_name}, I thought you might find this {resource.content_type} helpful: {resource.url}"

def increment_resource_usage(resource_id: UUID, user_id: UUID) -> bool:
    """
    Increment the usage count for a content resource.
    """
    try:
        with Session(engine) as session:
            resource = session.exec(
                select(ContentResource)
                .where(ContentResource.id == resource_id)
                .where(ContentResource.user_id == user_id)
            ).first()
            
            if resource:
                resource.usage_count = (resource.usage_count or 0) + 1
                session.add(resource)
                session.commit()
                return True
                
        return False
        
    except Exception as e:
        logging.error(f"Error incrementing resource usage: {e}", exc_info=True)
        return False 