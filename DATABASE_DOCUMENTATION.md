# AI Nudge Database Documentation

## Database Overview

**Database Name**: `ai_nudge` (PostgreSQL)  
**Database Engine**: PostgreSQL  
**ORM**: SQLModel (SQLAlchemy + Pydantic)  
**Migration Tool**: Alembic  
**Connection String**: `DATABASE_URL` environment variable

## Database Configuration

The database is configured through the `DATABASE_URL` environment variable, which typically follows this pattern:
```
postgresql://username:password@host:port/database_name
```

For local development, it's configured as:
```
postgresql://postgres:password123@db:5432/realestate_db
```

## Database Tables

The application contains **12 main tables**:

### 1. `user` Table
**Purpose**: Stores user account information and preferences
**Key Fields**:
- `id` (UUID, Primary Key)
- `user_type` (Enum: LOAN_OFFICER, etc.)
- `full_name` (String)
- `email` (String, indexed)
- `phone_number` (String, indexed, unique)
- `vertical` (String, indexed) - Business vertical (real_estate, therapy, etc.)
- `tool_provider` (String, indexed) - Integration tool factory key
- `onboarding_complete` (Boolean)
- `onboarding_state` (JSON) - Tracks onboarding progress
- `market_focus` (JSON) - List of market focus areas
- `ai_style_guide` (JSON) - AI personality preferences
- `strategy` (JSON) - User's communication strategy
- `mls_username`, `mls_password` (String) - MLS credentials
- `license_number` (String)
- `specialties` (JSON) - List of specialties
- `faq_auto_responder_enabled` (Boolean)
- `twilio_phone_number` (String, indexed)
- `timezone` (String, indexed)

### 2. `client` Table
**Purpose**: Stores client/contact information
**Key Fields**:
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to user.id, indexed)
- `full_name` (String)
- `email` (String, unique, indexed)
- `phone` (String, indexed)
- `notes` (Text) - Client notes
- `notes_embedding` (JSON) - Vector embedding of notes for semantic matching
- `ai_tags` (JSON) - AI-generated tags
- `user_tags` (JSON) - User-defined tags
- `preferences` (JSON) - Client preferences
- `last_interaction` (String)
- `timezone` (String)

### 3. `message` Table
**Purpose**: Stores all messages (sent and received)
**Key Fields**:
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to user.id, indexed)
- `client_id` (UUID, Foreign Key to client.id, indexed)
- `content` (String) - Message content
- `direction` (Enum: INBOUND, OUTBOUND, indexed)
- `status` (Enum: PENDING, SENT, FAILED, CANCELLED, RECEIVED)
- `source` (Enum: MANUAL, SCHEDULED, FAQ_AUTO_RESPONSE, INSTANT_NUDGE, indexed)
- `sender_type` (Enum: USER, AI, SYSTEM, indexed)
- `created_at` (DateTime, indexed)
- `originally_scheduled_at` (DateTime, indexed)

### 4. `scheduledmessage` Table
**Purpose**: Stores scheduled messages
**Key Fields**:
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to user.id, indexed)
- `client_id` (UUID, Foreign Key to client.id)
- `parent_plan_id` (UUID, Foreign Key to campaignbriefing.id, indexed)
- `content` (String)
- `scheduled_at_utc` (DateTime, indexed)
- `timezone` (String, indexed)
- `status` (Enum, indexed)
- `sent_at` (DateTime)
- `error_message` (String)
- `celery_task_id` (String, indexed)
- `created_at` (DateTime)
- `playbook_touchpoint_id` (String, indexed)
- `is_recurring` (Boolean, indexed)

### 5. `campaignbriefing` Table
**Purpose**: Stores AI-generated nudges and campaign plans
**Key Fields**:
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to user.id, indexed)
- `client_id` (UUID, Foreign Key to client.id, indexed)
- `triggering_resource_id` (UUID, Foreign Key to resource.id, indexed)
- `parent_message_id` (UUID, Foreign Key to message.id, indexed)
- `is_plan` (Boolean, indexed)
- `campaign_type` (String, indexed)
- `headline` (String)
- `key_intel` (JSON) - AI insights
- `matched_audience` (JSON) - Matched clients
- `original_draft` (String)
- `edited_draft` (String, optional) - User-edited version
- `status` (Enum: DRAFT, ACTIVE, PAUSED, COMPLETED, CANCELLED, DISMISSED, indexed)
- `created_at` (DateTime)
- `updated_at` (DateTime, auto-updated)

### 6. `resource` Table
**Purpose**: Stores various resources (properties, content, etc.)
**Key Fields**:
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to user.id, indexed)
- `resource_type` (Enum: PROPERTY, WEB_CONTENT, CONTENT_RESOURCE, indexed)
- `status` (Enum: ACTIVE, INACTIVE, ARCHIVED, indexed)
- `entity_id` (String, indexed) - External ID (listing key, URL, etc.)
- `attributes` (JSON) - Resource-specific attributes
- `created_at` (DateTime, indexed)
- `updated_at` (DateTime, indexed)

### 7. `contentresource` Table
**Purpose**: Stores manually added content resources
**Key Fields**:
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to user.id, indexed)
- `title` (String, indexed)
- `url` (String, indexed)
- `description` (String)
- `categories` (JSON) - Content categories
- `content_type` (String) - article, video, document, etc.
- `status` (Enum, indexed)
- `usage_count` (Integer, indexed) - How often used
- `created_at` (DateTime, indexed)
- `updated_at` (DateTime, indexed)

### 8. `marketevent` Table
**Purpose**: Stores user-specific market events
**Key Fields**:
- `id` (UUID, Primary Key, indexed)
- `user_id` (UUID, Foreign Key to user.id, indexed)
- `event_type` (String, indexed) - new_listing, price_change, etc.
- `entity_id` (String, indexed) - Original listing key from MLS
- `entity_type` (String) - Usually "property"
- `payload` (JSON) - Event data
- `market_area` (String)
- `status` (String, indexed) - unprocessed, processed, error
- `created_at` (DateTime, indexed)
- `processed_at` (DateTime)

### 9. `globalmlsevent` Table
**Purpose**: Stores raw MLS events (user-agnostic)
**Key Fields**:
- `id` (UUID, Primary Key, indexed)
- `source_id` (String, indexed) - MLS data source identifier
- `listing_key` (String, indexed) - Unique listing ID from MLS
- `raw_payload` (JSON) - Raw MLS API response
- `event_timestamp` (DateTime, indexed) - Event timestamp from source
- `created_at` (DateTime, indexed)

### 10. `pipelinerun` Table
**Purpose**: Tracks automated pipeline executions
**Key Fields**:
- `id` (UUID, Primary Key, indexed)
- `pipeline_type` (String) - Usually "main_opportunity_pipeline"
- `status` (String) - running, completed, failed
- `started_at` (DateTime)
- `completed_at` (DateTime)
- `events_processed` (Integer)
- `campaigns_created` (Integer)
- `errors` (String)
- `duration_seconds` (Float)
- `user_count` (Integer)

### 11. `faq` Table
**Purpose**: Stores FAQ entries for auto-responses
**Key Fields**:
- `id` (UUID, Primary Key)
- `user_id` (UUID, Foreign Key to user.id)
- `question` (String)
- `answer` (String)
- `is_enabled` (Boolean)

### 12. `negativepreference` Table
**Purpose**: Stores user feedback to avoid similar suggestions
**Key Fields**:
- `id` (UUID, Primary Key)
- `client_id` (UUID, Foreign Key to client.id, indexed)
- `dismissed_embedding` (JSON) - Vector embedding of dismissed opportunity
- `source_campaign_id` (UUID, indexed) - ID of dismissed campaign
- `created_at` (DateTime)

## Database Relationships

### Primary Relationships:
- **User** → **Client** (One-to-Many)
- **User** → **Message** (One-to-Many)
- **User** → **ScheduledMessage** (One-to-Many)
- **User** → **CampaignBriefing** (One-to-Many)
- **User** → **Resource** (One-to-Many)
- **User** → **ContentResource** (One-to-Many)
- **User** → **MarketEvent** (One-to-Many)
- **User** → **Faq** (One-to-Many)

- **Client** → **Message** (One-to-Many)
- **Client** → **ScheduledMessage** (One-to-Many)
- **Client** → **CampaignBriefing** (One-to-Many)
- **Client** → **NegativePreference** (One-to-Many)

- **Message** → **CampaignBriefing** (One-to-Many) - AI drafts
- **CampaignBriefing** → **ScheduledMessage** (One-to-Many)
- **Resource** → **CampaignBriefing** (One-to-Many) - Triggering resources

## Database Features

### 1. Multi-Vertical Support
- The database supports multiple business verticals (real estate, therapy, etc.)
- `user.vertical` field determines the business context
- `user.tool_provider` field specifies integration tools

### 2. Vector Embeddings
- `client.notes_embedding` stores semantic vectors for client matching
- `negativepreference.dismissed_embedding` stores vectors of dismissed opportunities

### 3. JSON Fields
- Extensive use of JSON fields for flexible data storage
- Supports complex nested data structures
- Used for attributes, preferences, tags, and configuration

### 4. Indexing Strategy
- Primary keys are UUIDs with indexes
- Foreign keys are indexed for performance
- Enum fields are indexed for filtering
- DateTime fields are indexed for time-based queries
- Composite indexes on frequently queried combinations

### 5. Migration History
The database uses Alembic for migrations with the following key migrations:
- `ea68fcacaed1_initial_database_schema.py` - Initial schema
- `357f39f135c0_add_explicit_tablename_to_.py` - Explicit table names
- `514e677f7478_add_super_user_field.py` - Super user functionality
- `6fced02bbabe_add_updated_at_to_campaignbriefing.py` - Campaign briefing timestamps
- `2ce7c9665fe8_add_pipeline_run_table.py` - Pipeline tracking
- `add_edited_draft_column.py` - Campaign briefing editing
- `add_flexmls_oauth_token_fields.py` - MLS OAuth integration
- `remove_flexmls_oauth_token_fields.py` - Cleanup of OAuth fields
- `add_negativepreference_table.py` - User feedback
- `e0664be3e4b6_add_globalmlsevent_table.py` - Global MLS events

## Database Statistics

- **Total Tables**: 12
- **Primary Tables**: 12 (all main tables)
- **Total Indexes**: 50+ (including composite indexes)
- **JSON Fields**: 15+ across all tables
- **UUID Primary Keys**: All tables
- **Foreign Key Relationships**: 20+ relationships

## Database Architecture Patterns

### 1. Event-Driven Architecture
- `globalmlsevent` stores raw events
- `marketevent` stores processed user-specific events
- `pipelinerun` tracks processing status

### 2. Multi-Tenant Design
- All tables include `user_id` for data isolation
- Vertical-specific data stored in JSON fields
- Tool provider configuration per user

### 3. AI/ML Integration
- Vector embeddings for semantic search
- JSON storage for AI-generated content
- Feedback loops for learning
- Campaign briefing status management (DRAFT, ACTIVE, PAUSED, etc.)

### 4. Message Pipeline
- `message` for actual messages
- `scheduledmessage` for future messages
- `campaignbriefing` for AI-generated content
- Celery integration for async processing

## Database Security

- UUID primary keys prevent enumeration attacks
- User-scoped data access (user_id foreign keys)
- Environment-based configuration
- No sensitive data in logs (configurable)

## Database Performance

- Indexed foreign keys for fast joins
- Indexed enum fields for filtering
- Indexed datetime fields for time-based queries
- JSON fields for flexible schema evolution
- Composite indexes for common query patterns

---

*This documentation covers the complete database structure of the AI Nudge application as of the current codebase state.* 