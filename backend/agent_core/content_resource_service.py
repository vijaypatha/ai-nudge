# backend/agent_core/content_resource_service.py
# Content resource service for integrating content recommendations into AI suggestions

import logging
from typing import List, Dict, Any
from uuid import UUID
from sqlmodel import Session, select
from difflib import SequenceMatcher

from data.models.resource import ContentResource, Resource
from data.models.client import Client
from data.database import engine
from agent_core.llm_client import get_chat_completion
from agent_core.llm_client import generate_embedding

def calculate_fuzzy_similarity(str1: str, str2: str) -> float:
    """
    Calculate fuzzy similarity between two strings using SequenceMatcher.
    Returns a value between 0 and 1, where 1 is an exact match.
    """
    return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()

def get_content_recommendations_for_user(user_id: UUID, use_fuzzy: bool = True, fuzzy_threshold: float = 0.8) -> List[Dict[str, Any]]:
    """
    Get content recommendations for a user as part of the AI suggestions system.
    This integrates content resources into the Perceive layer that feeds into AI reasoning.
    Now supports fuzzy matching and enhanced logging.
    """
    logging.info(f"CONTENT_RECOMMENDATIONS: Starting recommendations for user {user_id}")
    
    try:
        with Session(engine) as session:
            # Get all active content resources for the user
            content_resources = session.exec(
                select(ContentResource)
                .where(ContentResource.user_id == user_id)
                .where(ContentResource.status == 'active')
            ).all()
            
            # Get all active web_content resources for the user (for seeded data)
            web_resources = session.exec(
                select(Resource)
                .where(Resource.user_id == user_id)
                .where(Resource.status == 'active')
                .where(Resource.resource_type == 'web_content')
            ).all()
            
            all_resources = content_resources + web_resources
            
            logging.info(f"CONTENT_RECOMMENDATIONS: Found {len(content_resources)} content resources and {len(web_resources)} web resources")
            
            if not all_resources:
                logging.info(f"CONTENT_RECOMMENDATIONS: No active resources found for user {user_id}")
                return []
            
            # Get all clients for the user
            clients = session.exec(
                select(Client)
                .where(Client.user_id == user_id)
            ).all()
            
            logging.info(f"CONTENT_RECOMMENDATIONS: Processing {len(clients)} clients")
            
            recommendations = []
            total_matches = 0
            
            for resource in all_resources:
                # Find matching clients based on resource categories and client tags
                matched_clients = find_matching_clients_generic(resource, clients, use_fuzzy, fuzzy_threshold)
                
                if matched_clients:
                    total_matches += len(matched_clients)
                    # Generate personalized message for each matched client
                    for client in matched_clients:
                        message = generate_resource_message_sync_generic(resource, client)
                        
                        # Extract resource data based on type
                        if isinstance(resource, ContentResource):
                            resource_data = {
                                'id': resource.id,
                                'title': resource.title,
                                'description': resource.description,
                                'url': resource.url,
                                'categories': resource.categories,
                                'content_type': resource.content_type,
                                'created_at': resource.created_at,
                                'updated_at': resource.updated_at
                            }
                        else:  # Resource with web_content type
                            resource_data = {
                                'id': resource.id,
                                'title': resource.attributes.get('title', ''),
                                'description': resource.attributes.get('description', ''),
                                'url': resource.attributes.get('url', ''),
                                'categories': resource.attributes.get('categories', []),
                                'content_type': resource.attributes.get('content_type', 'article'),
                                'created_at': resource.created_at,
                                'updated_at': resource.updated_at
                            }
                        
                        recommendation = {
                            'resource': resource_data,
                            'matched_clients': [{
                                'client_id': client.id,
                                'client_name': client.full_name,
                                'match_reason': f"Matches categories: {', '.join(resource_data['categories'])}"
                            }],
                            'generated_message': message
                        }
                        recommendations.append(recommendation)
            
            logging.info(f"CONTENT_RECOMMENDATIONS: Generated {len(recommendations)} recommendations with {total_matches} total matches for user {user_id}")
            return recommendations
            
    except Exception as e:
        logging.error(f"CONTENT_RECOMMENDATIONS: Error getting content recommendations for user {user_id}: {e}", exc_info=True)
        return []

def find_matching_clients(resource: ContentResource, clients: List[Client], use_fuzzy: bool = True, fuzzy_threshold: float = 0.8) -> List[Client]:
    """
    Find clients that match the content resource based on categories and tags.
    Now supports case-insensitive matching and optional fuzzy matching.
    """
    matched_clients = []
    
    # Convert resource categories to lowercase for case-insensitive matching
    resource_categories = set(cat.lower() for cat in (resource.categories or []))
    
    logging.info(f"CONTENT_MATCHING: Processing resource '{resource.title}' with categories: {resource_categories}")
    
    for client in clients:
        # Convert client tags to lowercase for case-insensitive matching
        client_user_tags = set(tag.lower() for tag in (client.user_tags or []))
        client_ai_tags = set(tag.lower() for tag in (client.ai_tags or []))
        
        match_found = False
        match_type = "none"
        match_details = []
        
        # Check for exact matches first
        user_tag_matches = client_user_tags.intersection(resource_categories)
        ai_tag_matches = client_ai_tags.intersection(resource_categories)
        
        if user_tag_matches or ai_tag_matches:
            match_found = True
            match_type = "exact"
            if user_tag_matches:
                match_details.extend([f"user_tag:{tag}" for tag in user_tag_matches])
            if ai_tag_matches:
                match_details.extend([f"ai_tag:{tag}" for tag in ai_tag_matches])
        
        # If fuzzy matching is enabled and no exact match found, try fuzzy matching
        elif use_fuzzy:
            best_fuzzy_score = 0.0
            best_fuzzy_match = None
            
            # Check user tags against resource categories
            for client_tag in client_user_tags:
                for resource_category in resource_categories:
                    fuzzy_score = calculate_fuzzy_similarity(client_tag, resource_category)
                    if fuzzy_score > best_fuzzy_score and fuzzy_score >= fuzzy_threshold:
                        best_fuzzy_score = fuzzy_score
                        best_fuzzy_match = f"user_tag:{client_tag}->{resource_category}"
            
            # Check AI tags against resource categories
            for client_tag in client_ai_tags:
                for resource_category in resource_categories:
                    fuzzy_score = calculate_fuzzy_similarity(client_tag, resource_category)
                    if fuzzy_score > best_fuzzy_score and fuzzy_score >= fuzzy_threshold:
                        best_fuzzy_score = fuzzy_score
                        best_fuzzy_match = f"ai_tag:{client_tag}->{resource_category}"
            
            if best_fuzzy_match:
                match_found = True
                match_type = "fuzzy"
                match_details = [best_fuzzy_match]
        
        if match_found:
            matched_clients.append(client)
            logging.info(f"CONTENT_MATCHING: Match found for client '{client.full_name}' (ID: {client.id}) - Type: {match_type}, Details: {match_details}")
        else:
            logging.debug(f"CONTENT_MATCHING: No match for client '{client.full_name}' (ID: {client.id}) - User tags: {client_user_tags}, AI tags: {client_ai_tags}")
    
    logging.info(f"CONTENT_MATCHING: Found {len(matched_clients)} matches for resource '{resource.title}'")
    return matched_clients

def find_matching_clients_generic(resource, clients: List[Client], use_fuzzy: bool = True, fuzzy_threshold: float = 0.8) -> List[Client]:
    """
    Find clients that match the content resource based on categories and tags.
    Works with both ContentResource and Resource objects.
    Now supports case-insensitive matching and optional fuzzy matching.
    """
    matched_clients = []
    
    # Extract categories based on resource type and convert to lowercase
    if isinstance(resource, ContentResource):
        resource_categories = set(cat.lower() for cat in (resource.categories or []))
        resource_title = resource.title
    else:  # Resource with web_content type
        resource_categories = set(cat.lower() for cat in (resource.attributes.get('categories', []) or []))
        resource_title = resource.attributes.get('title', 'Unknown')
    
    logging.info(f"CONTENT_MATCHING_GENERIC: Processing resource '{resource_title}' with categories: {resource_categories}")
    
    for client in clients:
        # Convert client tags to lowercase for case-insensitive matching
        client_user_tags = set(tag.lower() for tag in (client.user_tags or []))
        client_ai_tags = set(tag.lower() for tag in (client.ai_tags or []))
        
        match_found = False
        match_type = "none"
        match_details = []
        
        # Check for exact matches first
        user_tag_matches = client_user_tags.intersection(resource_categories)
        ai_tag_matches = client_ai_tags.intersection(resource_categories)
        
        if user_tag_matches or ai_tag_matches:
            match_found = True
            match_type = "exact"
            if user_tag_matches:
                match_details.extend([f"user_tag:{tag}" for tag in user_tag_matches])
            if ai_tag_matches:
                match_details.extend([f"ai_tag:{tag}" for tag in ai_tag_matches])
        
        # If fuzzy matching is enabled and no exact match found, try fuzzy matching
        elif use_fuzzy:
            best_fuzzy_score = 0.0
            best_fuzzy_match = None
            
            # Check user tags against resource categories
            for client_tag in client_user_tags:
                for resource_category in resource_categories:
                    fuzzy_score = calculate_fuzzy_similarity(client_tag, resource_category)
                    if fuzzy_score > best_fuzzy_score and fuzzy_score >= fuzzy_threshold:
                        best_fuzzy_score = fuzzy_score
                        best_fuzzy_match = f"user_tag:{client_tag}->{resource_category}"
            
            # Check AI tags against resource categories
            for client_tag in client_ai_tags:
                for resource_category in resource_categories:
                    fuzzy_score = calculate_fuzzy_similarity(client_tag, resource_category)
                    if fuzzy_score > best_fuzzy_score and fuzzy_score >= fuzzy_threshold:
                        best_fuzzy_score = fuzzy_score
                        best_fuzzy_match = f"ai_tag:{client_tag}->{resource_category}"
            
            if best_fuzzy_match:
                match_found = True
                match_type = "fuzzy"
                match_details = [best_fuzzy_match]
        
        if match_found:
            matched_clients.append(client)
            logging.info(f"CONTENT_MATCHING_GENERIC: Match found for client '{client.full_name}' (ID: {client.id}) - Type: {match_type}, Details: {match_details}")
        else:
            logging.debug(f"CONTENT_MATCHING_GENERIC: No match for client '{client.full_name}' (ID: {client.id}) - User tags: {client_user_tags}, AI tags: {client_ai_tags}")
    
    logging.info(f"CONTENT_MATCHING_GENERIC: Found {len(matched_clients)} matches for resource '{resource_title}'")
    return matched_clients

async def find_matching_clients_semantic(resource: ContentResource, clients: List[Client], similarity_threshold: float = 0.7) -> List[Client]:
    """
    Find clients that match the content resource using semantic embeddings.
    This provides more intelligent matching based on content meaning, not just exact string matches.
    """
    try:
        matched_clients = []
        
        # Create embedding for the resource content
        resource_text = f"{resource.title} {resource.description or ''}"
        resource_embedding = await generate_embedding(resource_text)
        
        for client in clients:
            # Create embedding for client profile
            client_tags = (client.user_tags or []) + (client.ai_tags or [])
            client_notes = client.notes or ""
            client_text = f"{client.full_name} {' '.join(client_tags)} {client_notes}"
            client_embedding = await generate_embedding(client_text)
            
            # Calculate cosine similarity
            similarity = calculate_cosine_similarity(resource_embedding, client_embedding)
            
            if similarity >= similarity_threshold:
                logging.info(f"Semantic match found: {client.full_name} -> {resource.title} (similarity: {similarity:.3f})")
                matched_clients.append(client)
        
        return matched_clients
        
    except Exception as e:
        logging.error(f"Error in semantic matching: {e}", exc_info=True)
        # Fallback to exact matching if semantic matching fails
        return find_matching_clients(resource, clients)

def calculate_cosine_similarity(embedding1: List[float], embedding2: List[float]) -> float:
    """
    Calculate cosine similarity between two embeddings.
    """
    import numpy as np
    
    vec1 = np.array(embedding1)
    vec2 = np.array(embedding2)
    
    # Calculate cosine similarity
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    
    if norm1 == 0 or norm2 == 0:
        return 0.0
    
    return dot_product / (norm1 * norm2)

async def get_content_recommendations_semantic(user_id: UUID, use_semantic: bool = True) -> List[Dict[str, Any]]:
    """
    Get content recommendations using semantic matching when enabled.
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
                if use_semantic:
                    # Use semantic matching
                    matched_clients = await find_matching_clients_semantic(resource, clients)
                else:
                    # Use exact matching
                    matched_clients = find_matching_clients(resource, clients)
                
                if matched_clients:
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
                                'match_reason': f"Semantic match (similarity: {calculate_cosine_similarity([], []) if use_semantic else 'exact match'})"
                            }],
                            'generated_message': message
                        }
                        recommendations.append(recommendation)
            
            return recommendations
            
    except Exception as e:
        logging.error(f"Error getting semantic content recommendations for user {user_id}: {e}", exc_info=True)
        return []

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

def generate_resource_message_sync_generic(resource, client: Client) -> str:
    """
    Generate a personalized message for sharing content with a client (synchronous version).
    Works with both ContentResource and Resource objects.
    """
    try:
        # Create a simple personalized message without LLM for now
        client_name = client.full_name.split()[0] if client.full_name else "there"
        
        # Extract resource data based on type
        if isinstance(resource, ContentResource):
            content_type = resource.content_type
            categories = resource.categories or []
            description = resource.description
            url = resource.url
        else:  # Resource with web_content type
            content_type = resource.attributes.get('content_type', 'article')
            categories = resource.attributes.get('categories', []) or []
            description = resource.attributes.get('description', '')
            url = resource.attributes.get('url', '')
        
        if content_type == "video":
            base_message = f"I found a helpful video about {', '.join(categories)} that might be useful."
        elif content_type == "document":
            base_message = f"I have a helpful guide about {', '.join(categories)} that includes practical strategies."
        else:  # article or default
            base_message = f"I found a helpful article about {', '.join(categories)} that might be useful."
        
        if description:
            base_message += f" {description}"
        
        base_message += f"\n\nHere's the link: {url}"
        base_message += "\n\nLet me know if you find it helpful!"
        
        return f"Hi {client_name}, {base_message}"
        
    except Exception as e:
        logging.error(f"Error generating resource message: {e}", exc_info=True)
        # Fallback message
        return f"Hi {client.full_name}, I thought you might find this content helpful."

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