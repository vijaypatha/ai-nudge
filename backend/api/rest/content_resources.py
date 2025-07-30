# ---
# File Path: backend/api/rest/content_resources.py
# ---

import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from data.database import get_session
from data.models.user import User
from data.models.resource import ContentResource, ContentResourceCreate, ContentResourceUpdate
from api.security import get_current_user_from_token
from data import crm as crm_service

router = APIRouter()

@router.get("/", response_model=List[ContentResource])
async def get_content_resources(
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    """
    Get all content resources for the current user.
    """
    logging.info(f"API: Getting content resources for user '{current_user.id}'")
    
    statement = select(ContentResource).where(
        ContentResource.user_id == current_user.id,
        ContentResource.status == "active"
    )
    resources = session.exec(statement).all()
    
    logging.info(f"API: Found {len(resources)} content resources for user '{current_user.id}'")
    return resources

@router.post("/", response_model=ContentResource)
async def create_content_resource(
    resource_data: ContentResourceCreate,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    """
    Create a new content resource for the current user.
    """
    logging.info(f"API: Creating content resource for user '{current_user.id}'")
    
    # Create the content resource
    new_resource = ContentResource(
        user_id=current_user.id,
        **resource_data.model_dump()
    )
    
    session.add(new_resource)
    session.commit()
    session.refresh(new_resource)
    
    logging.info(f"API: Created content resource '{new_resource.id}' for user '{current_user.id}'")
    return new_resource

@router.put("/{resource_id}", response_model=ContentResource)
async def update_content_resource(
    resource_id: UUID,
    resource_data: ContentResourceUpdate,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    """
    Update an existing content resource.
    """
    logging.info(f"API: Updating content resource '{resource_id}' for user '{current_user.id}'")
    
    # Get the resource
    statement = select(ContentResource).where(
        ContentResource.id == resource_id,
        ContentResource.user_id == current_user.id
    )
    resource = session.exec(statement).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Content resource not found")
    
    # Update the resource
    update_data = resource_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(resource, field, value)
    
    session.add(resource)
    session.commit()
    session.refresh(resource)
    
    logging.info(f"API: Updated content resource '{resource_id}' for user '{current_user.id}'")
    return resource

@router.delete("/{resource_id}")
async def delete_content_resource(
    resource_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    """
    Delete a content resource (soft delete by setting status to archived).
    """
    logging.info(f"API: Deleting content resource '{resource_id}' for user '{current_user.id}'")
    
    # Get the resource
    statement = select(ContentResource).where(
        ContentResource.id == resource_id,
        ContentResource.user_id == current_user.id
    )
    resource = session.exec(statement).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Content resource not found")
    
    # Soft delete by setting status to archived
    resource.status = "archived"
    session.add(resource)
    session.commit()
    
    logging.info(f"API: Deleted content resource '{resource_id}' for user '{current_user.id}'")
    return {"message": "Content resource deleted successfully"}

@router.get("/suggestions/{client_id}", response_model=List[ContentResource])
async def get_content_suggestions_for_client(
    client_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session),
    use_fuzzy: bool = True,
    fuzzy_threshold: float = 0.8
):
    """
    Get content resource suggestions for a specific client based on their tags and interests.
    Now supports fuzzy matching and case-insensitive matching.
    """
    logging.info(f"API_CONTENT_SUGGESTIONS: Getting content suggestions for client '{client_id}' and user '{current_user.id}' (fuzzy={use_fuzzy}, threshold={fuzzy_threshold})")
    
    # Get the client
    client = crm_service.get_client_by_id(client_id, current_user.id)
    if not client:
        logging.warning(f"API_CONTENT_SUGGESTIONS: Client '{client_id}' not found for user '{current_user.id}'")
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Get client tags (both user-set and AI-extracted) - already case-insensitive
    client_tags = []
    if client.user_tags:
        client_tags.extend([tag.lower() for tag in client.user_tags])
    if client.ai_tags:
        client_tags.extend([tag.lower() for tag in client.ai_tags])
    
    logging.info(f"API_CONTENT_SUGGESTIONS: Client '{client.full_name}' has {len(client_tags)} tags: {client_tags}")
    
    if not client_tags:
        logging.info(f"API_CONTENT_SUGGESTIONS: No tags found for client '{client_id}', returning empty suggestions")
        return []
    
    # Get active content resources for the user
    statement = select(ContentResource).where(
        ContentResource.user_id == current_user.id,
        ContentResource.status == "active"
    )
    all_resources = session.exec(statement).all()
    
    logging.info(f"API_CONTENT_SUGGESTIONS: Found {len(all_resources)} active resources for user '{current_user.id}'")
    
    # Enhanced matching with fuzzy support
    suggested_resources = []
    from difflib import SequenceMatcher
    
    def calculate_fuzzy_similarity(str1: str, str2: str) -> float:
        """Calculate fuzzy similarity between two strings."""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    for resource in all_resources:
        resource_categories = [cat.lower() for cat in resource.categories]
        match_found = False
        match_type = "none"
        
        # Check for exact matches first
        for client_tag in client_tags:
            for resource_category in resource_categories:
                if client_tag == resource_category:
                    match_found = True
                    match_type = "exact"
                    break
            if match_found:
                break
        
        # If no exact match and fuzzy matching is enabled, try fuzzy matching
        if not match_found and use_fuzzy:
            for client_tag in client_tags:
                for resource_category in resource_categories:
                    fuzzy_score = calculate_fuzzy_similarity(client_tag, resource_category)
                    if fuzzy_score >= fuzzy_threshold:
                        match_found = True
                        match_type = "fuzzy"
                        logging.info(f"API_CONTENT_SUGGESTIONS: Fuzzy match found for client '{client.full_name}' - '{client_tag}' -> '{resource_category}' (score: {fuzzy_score:.3f})")
                        break
                if match_found:
                    break
        
        if match_found:
            suggested_resources.append(resource)
            logging.info(f"API_CONTENT_SUGGESTIONS: Match found for resource '{resource.title}' - Type: {match_type}")
    
    # Sort by usage count (most used first) and then by creation date
    suggested_resources.sort(key=lambda x: (x.usage_count, x.created_at), reverse=True)
    
    logging.info(f"API_CONTENT_SUGGESTIONS: Found {len(suggested_resources)} content suggestions for client '{client_id}'")
    return suggested_resources

@router.post("/{resource_id}/increment-usage")
async def increment_resource_usage(
    resource_id: UUID,
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    """
    Increment the usage count for a content resource.
    """
    logging.info(f"API: Incrementing usage for content resource '{resource_id}' for user '{current_user.id}'")
    
    # Get the resource
    statement = select(ContentResource).where(
        ContentResource.id == resource_id,
        ContentResource.user_id == current_user.id
    )
    resource = session.exec(statement).first()
    
    if not resource:
        raise HTTPException(status_code=404, detail="Content resource not found")
    
    # Increment usage count
    resource.usage_count += 1
    session.add(resource)
    session.commit()
    
    logging.info(f"API: Incremented usage for content resource '{resource_id}' for user '{current_user.id}'")
    return {"message": "Usage count incremented successfully"}

@router.get("/recommendations")
async def get_content_recommendations(
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session),
    use_fuzzy: bool = True,
    fuzzy_threshold: float = 0.8
):
    """
    Get content recommendations for all clients of the user.
    Now supports fuzzy matching and case-insensitive matching.
    """
    logging.info(f"API_CONTENT_RECOMMENDATIONS: Getting content recommendations for user '{current_user.id}' (fuzzy={use_fuzzy}, threshold={fuzzy_threshold})")
    
    try:
        # Get all active content resources for the user
        statement = select(ContentResource).where(
            ContentResource.user_id == current_user.id,
            ContentResource.status == "active"
        )
        all_resources = session.exec(statement).all()
        
        logging.info(f"API_CONTENT_RECOMMENDATIONS: Found {len(all_resources)} active resources for user '{current_user.id}'")
        
        if not all_resources:
            logging.info(f"API_CONTENT_RECOMMENDATIONS: No active resources found for user '{current_user.id}'")
            return {
                "recommendations": [],
                "display_config": {
                    "article": {"icon": "BookOpen", "color": "text-blue-400", "title": "Article"},
                    "video": {"icon": "Video", "color": "text-purple-400", "title": "Video"},
                    "document": {"icon": "FileText", "color": "text-orange-400", "title": "Document"}
                }
            }
        
        # Get all clients for the user
        from data.models.client import Client
        clients = session.exec(select(Client).where(Client.user_id == current_user.id)).all()
        
        logging.info(f"API_CONTENT_RECOMMENDATIONS: Processing {len(clients)} clients")
        
        recommendations = []
        from difflib import SequenceMatcher
        
        def calculate_fuzzy_similarity(str1: str, str2: str) -> float:
            """Calculate fuzzy similarity between two strings."""
            return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
        
        for resource in all_resources:
            matched_clients = []
            
            for client in clients:
                # Get client tags (both user-set and AI-extracted) - already case-insensitive
                client_tags = []
                if client.user_tags:
                    client_tags.extend([tag.lower() for tag in client.user_tags])
                if client.ai_tags:
                    client_tags.extend([tag.lower() for tag in client.ai_tags])
                
                if not client_tags:
                    continue
                
                # Enhanced matching with fuzzy support
                matching_tags = []
                resource_categories = [cat.lower() for cat in resource.categories]
                match_found = False
                match_type = "none"
                
                # Check for exact matches first
                for client_tag in client_tags:
                    for resource_category in resource_categories:
                        if client_tag == resource_category:
                            matching_tags.append(client_tag)
                            match_found = True
                            match_type = "exact"
                            break
                    if match_found:
                        break
                
                # If no exact match and fuzzy matching is enabled, try fuzzy matching
                if not match_found and use_fuzzy:
                    for client_tag in client_tags:
                        for resource_category in resource_categories:
                            fuzzy_score = calculate_fuzzy_similarity(client_tag, resource_category)
                            if fuzzy_score >= fuzzy_threshold:
                                matching_tags.append(client_tag)
                                match_found = True
                                match_type = "fuzzy"
                                logging.info(f"API_CONTENT_RECOMMENDATIONS: Fuzzy match found for client '{client.full_name}' - '{client_tag}' -> '{resource_category}' (score: {fuzzy_score:.3f})")
                                break
                        if match_found:
                            break
                
                if matching_tags:
                    matched_clients.append({
                        "client_id": str(client.id),
                        "client_name": client.full_name,
                        "matching_tags": matching_tags,
                        "match_type": match_type
                    })
                    logging.info(f"API_CONTENT_RECOMMENDATIONS: Match found for client '{client.full_name}' with resource '{resource.title}' - Type: {match_type}, Tags: {matching_tags}")
            
            if matched_clients:
                recommendations.append({
                    "resource": {
                        "id": str(resource.id),
                        "title": resource.title,
                        "url": resource.url,
                        "description": resource.description,
                        "categories": resource.categories,
                        "content_type": resource.content_type,
                        "status": resource.status,
                        "usage_count": resource.usage_count,
                        "created_at": resource.created_at.isoformat(),
                        "updated_at": resource.updated_at.isoformat()
                    },
                    "matched_clients": matched_clients,
                    "total_matches": len(matched_clients)
                })
        
        # Sort by total matches (most matches first) and then by usage count
        recommendations.sort(key=lambda x: (x["total_matches"], x["resource"]["usage_count"]), reverse=True)
        
        display_config = {
            "article": {"icon": "BookOpen", "color": "text-blue-400", "title": "Article"},
            "video": {"icon": "Video", "color": "text-purple-400", "title": "Video"},
            "document": {"icon": "FileText", "color": "text-orange-400", "title": "Document"}
        }
        
        logging.info(f"API_CONTENT_RECOMMENDATIONS: Generated {len(recommendations)} recommendations for user '{current_user.id}'")
        return {
            "recommendations": recommendations,
            "display_config": display_config
        }
        
    except Exception as e:
        logging.error(f"API_CONTENT_RECOMMENDATIONS: Error getting content recommendations for user '{current_user.id}': {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get content recommendations")

@router.post("/{resource_id}/send-to-clients")
async def send_content_to_clients(
    resource_id: UUID,
    client_ids: List[str],
    current_user: User = Depends(get_current_user_from_token),
    session: Session = Depends(get_session)
):
    """
    Send a content resource to multiple clients.
    """
    logging.info(f"API: Sending content resource '{resource_id}' to {len(client_ids)} clients for user '{current_user.id}'")
    
    try:
        # Get the resource
        resource = session.exec(
            select(ContentResource)
            .where(ContentResource.id == resource_id)
            .where(ContentResource.user_id == current_user.id)
        ).first()
        
        if not resource:
            raise HTTPException(status_code=404, detail="Content resource not found")
        
        # Get the clients
        from data.models.client import Client
        clients = session.exec(
            select(Client)
            .where(Client.id.in_(client_ids))
            .where(Client.user_id == current_user.id)
        ).all()
        
        if not clients:
            raise HTTPException(status_code=404, detail="No valid clients found")
        
        # Generate personalized messages for each client
        from agent_core.content_resource_service import generate_resource_message
        from data.models.message import Message
        from uuid import uuid4
        from datetime import datetime, timezone
        
        for client in clients:
            # Generate personalized message
            message_content = generate_resource_message(resource, client)
            
            # Create and save the message
            message = Message(
                id=uuid4(),
                client_id=client.id,
                user_id=current_user.id,
                content=message_content,
                direction='outbound',
                status='sent',
                created_at=datetime.now(timezone.utc),
                source='content_resource',
                sender_type='user'
            )
            session.add(message)
        
        # Increment usage count
        resource.usage_count += len(clients)
        session.add(resource)
        session.commit()
        
        logging.info(f"API: Successfully sent content resource '{resource_id}' to {len(clients)} clients")
        return {"message": f"Content sent to {len(clients)} clients successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"API: Error sending content resource '{resource_id}' to clients: {str(e)}")
        session.rollback()
        raise HTTPException(status_code=500, detail="Failed to send content to clients") 