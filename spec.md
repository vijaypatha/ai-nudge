# AI Nudge - Project Specification
**Last Updated**: 09/21/2025


## **Product Vision & Architecture**

### **1. Vision Statement**

To empower every business owner to effortlessly cultivate deeper, more meaningful customer relationships and drive sustainable growth through intelligent, proactive, and personalized AI-driven engagement.

, AI Nudge is NOT just a realtor app. Here's what I found:
Multi-Vertical Platform
AI Nudge is designed as a flexible core engine that can serve multiple business verticals through pluggable integrations:
Current Verticals Supported:
Real Estate - MLS integrations, property alerts, market updates
Therapy - HIPAA compliance, appointment reminders, wellness check-ins
Architecture Evidence:
backend/agent_core/verticals/ - Contains industry-specific logic
backend/workflow/playbooks/ - Has real_estate.py and therapy.py
Flexible Core Engine - The Event -> Audience -> Campaign architecture is abstract and can be adapted to any business
Key Design Principles:
"Flexible Core Engine for Any Business" - The underlying architecture is abstract
Pluggable Integrations - By plugging in different integrations (MLS, EHS, POS), we can serve any small business vertical
Industry-Specific Adaptations - Each vertical gets customized features while sharing the core AI intelligence
What Makes It Multi-Vertical:
Abstract Event Processing - The system detects events and finds relevant clients regardless of industry
Adaptable AI - The AI co-pilot learns from user actions and adapts to different business contexts
Modular Integrations - Different business tools can be plugged in (MLS for real estate, EHS for healthcare, POS for retail, etc.)
So while real estate is one of the primary verticals (and likely the first one developed), AI Nudge is fundamentally a business relationship automation platform that can serve any small business owner who wants to cultivate deeper customer relationships through intelligent, proactive engagement.
The real estate focus you might see in the codebase is likely because it was the initial vertical, but the architecture is designed to expand to therapy, retail, consulting, and other service-based businesses.

### **2. Core Principles (The "Why")**

- **Proactive Intelligence Layer, Not a Reactive CRM:** We do not store data for its own sake. Our system finds and acts on opportunities within the user's existing data, turning information into revenue.
    
- **Automation That Adapts to the User:** The AI co-pilot learns from the owner's actions—like their message edits—to adapt its style and provide a "Freedom with a Reason to Believe" experience.
    
- **Flexible Core Engine for Any Business:** The underlying architecture (`Event -> Audience -> Campaign`) is abstract. By plugging in different integrations (MLS, EHS, POS), we can serve any small business vertical.

- **Unified AI Experience:** Content recommendations are integrated into the AI suggestions system, not as a separate feature. This follows the "Perceive -> Reason -> Act -> Learn" framework where content resources are part of the Perceive layer that feeds into AI reasoning.

### **3. The Core Product Loop**

This is the fundamental engine of the application:

1. **Event Happens:** A market, relationship, or communication event occurs.
2. **AI Detects Who Cares:** The system finds clients who are a good fit for the event.
3. **AI Drafts the Campaign:** The AI generates a strategic "Campaign Briefing."
4. **Owner Approves and Refines:** The owner has full control to edit the message, audience, and timing.
5. **Multi-Channel Send:** The system executes the campaign (starting SMS-first).
6. **Customer Acts:** The client receives a relevant message and engages.
7. **Value Captured & The Loop Closes:** The system logs the outcome and learns from the interaction to improve future nudges.

### **4. Architectural Framework: Perceive -> Reason -> Act -> Learn**

- **Perceive (The Senses):** The `integrations` layer connects to the outside world to sense events.
- **Reason (The Brain):** The `agent_core/brain` and `workflow` layers do the high-level thinking, deciding what to do.
- **Act (The Hands & Mouth):** The `agent_core/agents` and `tools` layers execute tasks delegated by the brain, like drafting messages.
- **Learn (The Memory):** The `personalization` layer closes the loop, adapting the AI's performance and style over time.

---

## **Technical Architecture**

### **Backend Stack**
- **Framework:** FastAPI (Python 3.11)
- **Database:** PostgreSQL with SQLModel/SQLAlchemy ORM
- **Message Queue:** Redis + Celery for async task processing
- **AI/ML:** OpenAI API + Google Generative AI
- **Communication:** Twilio for SMS/voice
- **Authentication:** JWT with OAuth2 (Google)
- **Real-time:** WebSocket connections for live updates

### **Frontend Stack**
- **Framework:** Next.js 14 with React 18
- **Styling:** Tailwind CSS
- **State Management:** React Context + custom hooks
- **UI Components:** Custom components with Framer Motion
- **Authentication:** Client-side JWT management
- **Real-time:** WebSocket client integration

### **Infrastructure**
- **Containerization:** Docker + Docker Compose
- **Development:** Local development with hot reloading
- **Deployment:** Render.com (backend) + Vercel (frontend)
- **Monitoring:** Built-in logging and observability

---

## **Core Modules & Responsibilities**

### **Backend Structure**

#### **API Layer (`/api/`)**
- **`main.py`:** FastAPI application entry point with CORS and middleware
- **`rest/`:** REST API endpoints organized by domain (20+ endpoint categories)
- **`security.py`:** JWT authentication and user management
- **`websocket_manager.py`:** Real-time communication handling
- **`vercel_handler.py`:** Vercel deployment handler
- **`webhooks/`:** Webhook handlers for external services

#### **Complete API Endpoint Categories**
- **Authentication (`/auth`):** User login, registration, OAuth integration
- **User Management (`/users`):** Profile management, preferences, settings
- **Client Management (`/clients`):** CRUD operations, import, deduplication
- **Campaign Management (`/campaigns`):** Campaign creation, approval, execution
- **Conversation Management (`/conversations`):** Message handling, search, scheduling
- **Nudge Management (`/nudges`):** AI-generated nudge recommendations
- **Survey System (`/surveys`):** Template management, response processing
- **Portal System (`/portal`):** Secure portal generation and management
- **Content Resources (`/content-resources`):** Resource management and recommendations
- **MLS Integration (`/mls`):** Real estate data integration and testing
- **Twilio Integration (`/twilio-numbers`):** Phone number management and SMS
- **Scheduled Messages (`/scheduled-messages`):** Message scheduling and management
- **Community Features (`/community`):** User community and sharing
- **Admin Functions (`/admin`):** System administration and triggers
- **Settings Management (`/settings`):** User preferences and configuration
- **Inbox Management (`/inbox`):** Incoming message handling
- **FAQ Management (`/faqs`):** Frequently asked questions
- **WebSocket Support (`/ws`):** Real-time communication

#### **Agent Core (`/agent_core/`)**
- **`brain/`:** AI decision-making and reasoning engine
- **`agents/`:** Specialized AI agents for different tasks
- **`orchestrator.py`:** Coordinates between different AI components
- **`audience_builder.py`:** Client targeting and segmentation
- **`content_resource_service.py`:** Content recommendation and matching engine

#### **Data Layer (`/data/`)**
- **`models/`:** SQLModel database models
- **`database.py`:** Database connection and session management
- **`crm.py`:** Customer relationship management operations
- **`vector.py`:** Vector search and similarity matching
- **`models/resource.py`:** Content resource management and storage

#### **Integrations (`/integrations/`)**
- **`mls/`:** Multiple Listing Service integrations (FlexMLS Spark API, RESO API)
- **`twilio_*.py`:** SMS/voice communication
- **`oauth/google.py`:** Google OAuth for contact import
- **`openai.py`:** AI model integration
- **`tool_factory.py`:** Generic factory for vertical-specific tools

#### **Workflow (`/workflow/`)**
- **`actions.py`:** Reusable workflow actions
- **`campaigns.py`:** Campaign management and execution
- **`playbooks/`:** Industry-specific engagement strategies
- **`triggers.py`:** Event-driven workflow triggers

#### **Personalization (`/personalization/`)**
- **`context.py`:** User context and preferences
- **`intel.py`:** Client intelligence and insights
- **`profiler.py`:** User behavior profiling
- **`style.py`:** Communication style adaptation

### **Frontend Structure**

#### **App Router (`/app/`)**
- **`(main)/`:** Main application pages (dashboard, conversations, etc.)
- **`auth/`:** Authentication flows
- **`onboarding/`:** User onboarding process
- **`layout.tsx`:** Root layout with providers

#### **Components (`/components/`)**
- **`conversation/`:** Chat and messaging components
- **`nudges/`:** Nudge management and display
- **`client-intake/`:** Contact import and management
- **`ui/`:** Reusable UI components

#### **Context (`/context/`)**
- **`AppContext.tsx`:** Global application state
- **`SidebarContext.tsx`:** Navigation and sidebar state

---

## **Key Features & Capabilities**

### **1. Intelligent Client Management**
- **Contact Import:** Google OAuth integration for contact import
- **Client Profiling:** AI-powered client intelligence and segmentation
- **Relationship Tracking:** Automated relationship strength assessment
- **Deduplication:** Smart contact deduplication and merging

### **2. AI-Powered Campaigns**
- **Event Detection:** Automated market and relationship event detection
- **Audience Targeting:** Intelligent client targeting based on events
- **Message Drafting:** AI-generated personalized message drafts
- **Campaign Approval:** Owner review and editing workflow
- **Multi-channel Execution:** SMS-first with expansion to other channels

### **3. Real-time Communication**
- **Live Chat:** Real-time conversation management
- **Message History:** Complete conversation tracking
- **AI Co-pilot:** Intelligent message suggestions and responses
- **Scheduled Messages:** Future message scheduling and automation

### **4. Industry-Specific Adaptations**
- **Real Estate:** MLS integration, property alerts, market updates
- **Therapy:** HIPAA compliance, appointment reminders, wellness check-ins
- **Extensible:** Framework for additional verticals

### **5. Content Resource Management & Recommendations**
- **Content Resource Management:** Business owners can add trusted content URLs/documents in their profile settings
- **AI-Powered Matching:** Content recommendations based on client tags and resource categories
- **Integrated AI Suggestions:** Content recommendations appear in the main AI Suggestions tab alongside traditional opportunities
- **Perceive Layer Integration:** Content resources are part of the Perceive layer that feeds into the AI reasoning engine
- **Personalized Messaging:** AI generates personalized messages for sharing content with matched clients
- **Multi-Vertical Support:** Content resources work across all business verticals (real estate, therapy, consulting, etc.)
- **Usage Tracking:** System tracks which content resources are shared and their engagement rates
- **Content Categories:** Flexible categorization system for organizing content by topic and relevance
- **Client Matching Logic:** 
  - Matches clients based on user tags and AI tags
  - Considers resource categories and client interests
  - Supports multiple content types (documents, videos, articles)
- **Unified Experience:** Content recommendations appear in the same interface as other AI suggestions, providing a cohesive user experience

### **6. Client Intake Surveys**
- **Automated Survey Delivery:** System automatically sends intake surveys to new clients via SMS
- **Survey Templates:** Configurable survey templates for different verticals (real estate, therapy)
- **Multi-Step Surveys:** Support for complex, multi-step survey flows with various question types
- **AI Processing:** Survey responses are automatically processed by AI to extract client preferences and generate tags
- **Client Profiling:** Survey data feeds into the client intelligence engine for better matching
- **Manual Survey Management:** Agents can manually trigger surveys and customize survey messages
- **Survey Completion Tracking:** System tracks survey completion status and timing
- **Vertical-Specific Questions:** Different survey types for different business verticals (buyer vs seller surveys for real estate)

### **7. Interactive Client Portals**
- **Secure Portal Generation:** Real estate agents can generate secure, shareable portal links for clients
- **Property Curation:** AI-curated property matches are displayed in an interactive portal interface
- **Client Feedback Collection:** Clients can provide feedback on properties (like/dislike, comments)
- **Real-time Updates:** Portal content updates automatically as new matches are found
- **Multi-Media Support:** Property portals display photos, details, and agent commentary
- **Comment System:** Two-way commenting system between agents and clients on specific properties
- **Portal Analytics:** Track client engagement and feedback on portal content
- **Secure Access:** JWT-based secure access with expiration dates for portal links
- **Mobile-Responsive:** Portal interface works seamlessly on mobile devices
- **Agent Commentary:** AI-generated commentary explains why each property was selected for the client

### **8. Advanced Personalization & AI Learning System**
- **Style Adaptation:** AI learns from user message edits and adapts communication style
- **Behavior Profiling:** Comprehensive user interaction pattern analysis
- **Performance Optimization:** Continuous improvement based on campaign outcomes
- **Client Intelligence Engine:** AI-powered client profiling and segmentation
- **Context Awareness:** Dynamic adaptation to user context and preferences
- **Learning Mechanisms:**
  - **Edit Analysis:** Learns from user modifications to AI-generated content
  - **Response Tracking:** Monitors client engagement and response patterns
  - **Success Pattern Recognition:** Identifies what works best for each user
  - **Style Guide Generation:** Creates personalized communication guidelines
- **Personalization Components:**
  - **User Context Management:** Tracks user preferences and business context
  - **Client Intelligence:** Builds detailed client profiles and preferences
  - **User Profiling:** Analyzes user behavior and communication patterns
  - **Style Adaptation:** Learns and adapts to user's communication style
- **AI Learning Features:**
  - **Message Edit Learning:** Analyzes differences between AI drafts and user edits
  - **Engagement Pattern Analysis:** Tracks what content and timing works best
  - **Success Metrics Tracking:** Monitors campaign performance and outcomes
  - **Adaptive Recommendations:** Improves suggestions based on user feedback

### **9. Seamless Timezone Scheduling**
- **Zero Timezone Complexity:** Users schedule messages in their local time without any timezone selection
- **Automatic Detection:** System automatically detects user's timezone from browser
- **Backend Handles Everything:** 
  - User picks time in their local timezone
  - Frontend sends local time + detected timezone to backend
  - Backend converts to UTC for storage
  - Backend handles all timezone conversions for delivery
- **Minimal Click Workflow:**
  1. Click "Schedule" → Opens modal with default time (30 min from now)
  2. Type message → Write the message content
  3. Pick time → Use the datetime picker (optional, default is fine)
  4. Click "Schedule Message" → Done!
- **Benefits:**
  - ✅ Zero timezone complexity for users
  - ✅ Automatic detection of user's timezone
  - ✅ Simple interface - just date/time picker
  - ✅ Backend handles everything - conversions, storage, delivery
  - ✅ Works globally - any timezone, any user
  - ✅ Minimal clicks - just pick time and send
  - ✅ Dead simple: pick a time, write a message, schedule it. Everything else is handled automatically by the system

### **10. Comprehensive API Ecosystem**
- **RESTful API Design:** Complete REST API with 20+ endpoint categories
- **Authentication & Security:** JWT-based authentication with OAuth2 integration
- **Real-time Communication:** WebSocket support for live updates
- **API Categories:**
  - **Authentication:** User login, registration, OAuth integration
  - **Client Management:** CRUD operations, import, deduplication
  - **Campaign Management:** Campaign creation, approval, execution
  - **Conversation Management:** Message handling, search, scheduling
  - **Survey System:** Template management, response processing
  - **Portal System:** Secure portal generation and management
  - **Content Resources:** Resource management and recommendations
  - **MLS Integration:** Real estate data integration
  - **Twilio Integration:** Phone number management and SMS
  - **Admin Functions:** System administration and triggers
  - **Community Features:** User community and sharing
  - **Settings Management:** User preferences and configuration

### **11. Advanced Workflow & Automation Engine**
- **Conversational Playbooks:** Industry-specific conversation flows
- **Relationship Planning:** Automated relationship nurturing sequences
- **Event Processing Pipeline:** Automated event detection and response
- **Campaign Automation:** Intelligent campaign generation and execution
- **Vertical-Specific Workflows:**
  - **Real Estate:** MLS integration, property alerts, market updates
  - **Therapy:** HIPAA-compliant workflows, appointment reminders
  - **Extensible Framework:** Easy addition of new business verticals
- **Playbook Types:**
  - **Long-term Nurture:** Ongoing relationship building
  - **Short-term Lead Conversion:** Immediate engagement strategies
  - **Personal Event Reminders:** Birthday, anniversary, holiday messages
  - **Custom Frequency Playbooks:** User-defined engagement schedules

### **12. AI Learning & Personalization System**
- **Style Adaptation:** AI learns from user message edits and adapts communication style
- **Behavior Profiling:** Analysis of user interaction patterns and preferences
- **Performance Optimization:** Continuous improvement based on campaign outcomes
- **Client Intelligence:** AI-powered client profiling and segmentation
- **Context Awareness:** Dynamic adaptation to user context and preferences
- **Learning Mechanisms:**
  - **Edit Analysis:** Learns from user modifications to AI-generated content
  - **Response Tracking:** Monitors client engagement and response patterns
  - **Success Pattern Recognition:** Identifies what works best for each user
  - **Style Guide Generation:** Creates personalized communication guidelines

---

## **Codebase Structure**

### **Project Tree Structure**

```
ai-nudge/
├── backend/                          # Python FastAPI Backend
│   ├── __init__.py
│   ├── agent_core/                   # Core AI Agent System
│   │   ├── __init__.py
│   │   ├── agents/                   # Specialized AI Agents
│   │   │   ├── __init__.py
│   │   │   ├── conversation.py       # Conversation management agent
│   │   │   ├── guidance.py          # Guidance and recommendations
│   │   │   ├── profiler.py          # Client profiling agent
│   │   │   ├── relationship.py      # Relationship management
│   │   │   ├── scheduler.py         # Message scheduling
│   │   │   ├── survey.py            # Survey processing agent
│   │   │   └── verticals.py         # Vertical-specific logic
│   │   ├── audience_builder.py      # Client targeting and segmentation
│   │   ├── brain/                   # AI Decision Engine
│   │   │   ├── __init__.py
│   │   │   ├── nudge_engine.py      # Core nudge generation logic
│   │   │   ├── relationship_planner.py # Relationship planning
│   │   │   ├── semantic_service.py  # Semantic search and matching
│   │   │   └── verticals/           # Industry-specific AI logic
│   │   │       ├── __init__.py
│   │   │       ├── real_estate.py   # Real estate AI logic
│   │   │       └── therapy.py       # Therapy AI logic
│   │   ├── content_resource_service.py # Content recommendation engine
│   │   ├── deduplication/           # Contact deduplication
│   │   │   └── __init__.py
│   │   ├── llm_client.py           # LLM integration client
│   │   ├── orchestrator.py         # AI component coordination
│   │   ├── semantic_service.py     # Semantic search capabilities
│   │   ├── survey_config.py        # Survey configuration management
│   │   ├── survey_processor.py     # Survey response processing
│   │   └── tools/                  # AI tools and utilities
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── content.py
│   │       ├── conversation.py
│   │       └── relationship.py
│   ├── alembic/                    # Database migrations
│   │   ├── env.py
│   │   ├── README
│   │   ├── script.py.mako
│   │   └── versions/               # Migration files
│   │       └── [23 migration files]
│   ├── api/                        # API Layer
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── rest/                   # REST API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── admin_triggers.py   # Admin trigger endpoints
│   │   │   ├── api_endpoints.py    # Main API router
│   │   │   ├── auth.py             # Authentication endpoints
│   │   │   ├── campaigns.py        # Campaign management
│   │   │   ├── clients.py          # Client management
│   │   │   ├── community.py        # Community features
│   │   │   ├── conversations.py    # Conversation management
│   │   │   ├── content_resources.py # Content resource management
│   │   │   ├── faqs.py             # FAQ management
│   │   │   ├── inbox.py            # Inbox management
│   │   │   ├── mls.py              # MLS integration
│   │   │   ├── nudges.py           # Nudge management
│   │   │   ├── portal.py           # Portal system
│   │   │   ├── resources.py        # Resource management
│   │   │   ├── scheduled_messages.py # Message scheduling
│   │   │   ├── settings.py         # Settings management
│   │   │   ├── surveys.py          # Survey system
│   │   │   ├── twilio_numbers.py   # Twilio integration
│   │   │   ├── users.py            # User management
│   │   │   └── websockets.py       # WebSocket handling
│   │   ├── security.py             # Authentication and security
│   │   ├── vercel_handler.py       # Vercel deployment handler
│   │   └── webhooks/               # Webhook handlers
│   │       ├── __init__.py
│   │       └── twilio.py           # Twilio webhooks
│   ├── celery_beat_data/           # Celery beat scheduler data
│   ├── celery_tasks.py             # Celery task definitions
│   ├── celery_worker.py            # Celery worker configuration
│   ├── common/                     # Shared utilities
│   │   ├── __init__.py
│   │   ├── async_utils.py          # Async utility functions
│   │   ├── config.py               # Configuration management
│   │   ├── errors.py               # Error handling
│   │   ├── jwt_utils.py            # JWT token utilities
│   │   ├── log.py                  # Logging configuration
│   │   ├── redis_client.py         # Redis client
│   │   └── utils.py                # General utilities
│   ├── data/                       # Data Layer
│   │   ├── __init__.py
│   │   ├── crm.py                  # CRM operations
│   │   ├── database.py             # Database connection
│   │   ├── models/                 # Database models
│   │   │   ├── __init__.py
│   │   │   ├── campaign.py         # Campaign models
│   │   │   ├── client.py           # Client models
│   │   │   ├── event.py            # Event models
│   │   │   ├── message.py          # Message models
│   │   │   ├── portal.py           # Portal models
│   │   │   ├── resource.py         # Resource models
│   │   │   ├── survey.py           # Survey models
│   │   │   ├── user.py             # User models
│   │   │   └── [additional models]
│   │   ├── seed.py                 # Database seeding
│   │   └── vector.py               # Vector search
│   ├── integrations/               # External Integrations
│   │   ├── __init__.py
│   │   ├── calendar.py             # Calendar integration
│   │   ├── gemini.py               # Google Gemini AI
│   │   ├── google_search.py        # Google Search API
│   │   ├── mls/                    # MLS integrations
│   │   │   ├── __init__.py
│   │   │   ├── flexmls.py          # FlexMLS integration
│   │   │   ├── reso.py             # RESO API integration
│   │   │   └── [additional MLS files]
│   │   ├── oauth/                  # OAuth integrations
│   │   │   └── google.py           # Google OAuth
│   │   ├── openai.py               # OpenAI integration
│   │   ├── tool_factory.py         # Integration factory
│   │   ├── tool_interface.py       # Integration interface
│   │   ├── twilio_incoming.py      # Twilio incoming SMS
│   │   ├── twilio_otp.py           # Twilio OTP
│   │   └── twilio_outgoing.py      # Twilio outgoing SMS
│   ├── personalization/            # Personalization Engine
│   │   ├── __init__.py
│   │   ├── context.py              # User context
│   │   ├── intel.py                # Client intelligence
│   │   ├── profiler.py             # User profiling
│   │   └── style.py                # Style adaptation
│   ├── workflow/                   # Workflow Engine
│   │   ├── __init__.py
│   │   ├── actions.py              # Workflow actions
│   │   ├── campaigns.py            # Campaign workflows
│   │   ├── definitions.py          # Workflow definitions
│   │   ├── outbound.py             # Outbound messaging
│   │   ├── pipeline.py             # Main workflow pipeline
│   │   ├── playbooks/              # Industry playbooks
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Base playbook classes
│   │   │   ├── real_estate.py      # Real estate playbooks
│   │   │   └── therapy.py          # Therapy playbooks
│   │   ├── relationship_playbooks.py # Relationship playbooks
│   │   └── triggers.py             # Workflow triggers
│   ├── tests/                      # Test Suite
│   │   ├── test_auth.py
│   │   ├── test_campaigns.py
│   │   ├── test_clients.py
│   │   ├── test_community.py
│   │   ├── test_content_resource_service.py
│   │   ├── test_content_resources.py
│   │   ├── test_conversations.py
│   │   ├── test_database_schema.py
│   │   ├── test_live_reso_connection.py
│   │   ├── test_manual_contact_performance.py
│   │   ├── test_messaging.py
│   │   ├── test_migrations.py
│   │   ├── test_mls_integration.py
│   │   ├── test_orchestrator.py
│   │   ├── test_pipeline.py
│   │   ├── test_profiler.py
│   │   ├── test_scheduled_messages.py
│   │   ├── test_semantic_service.py
│   │   ├── test_simple_db.py
│   │   └── test_users.py
│   ├── alembic.ini                 # Alembic configuration
│   ├── conftest.py                 # Pytest configuration
│   ├── create_all_access_account_docker.sh
│   ├── create_all_access_account.sh
│   ├── create_super_user.py
│   ├── database_analysis_report.json
│   ├── database_analysis_simple.py
│   ├── database_analysis.py
│   ├── Dockerfile                  # Docker configuration
│   ├── env.example                 # Environment variables template
│   ├── pytest.ini                 # Pytest configuration
│   ├── README.md
│   ├── requirements-render.txt     # Production requirements
│   ├── requirements.txt            # Development requirements
│   ├── rescore_all.py
│   ├── start_render.sh
│   └── test.db                     # Test database
├── frontend/                       # Next.js Frontend
│   ├── app/                        # Next.js App Router
│   │   ├── (main)/                 # Main application pages
│   │   │   ├── clients/
│   │   │   ├── conversations/
│   │   │   ├── dashboard/
│   │   │   ├── nudges/
│   │   │   ├── portal/
│   │   │   ├── settings/
│   │   │   └── [additional pages]
│   │   ├── auth/                   # Authentication pages
│   │   │   ├── login/
│   │   │   ├── register/
│   │   │   └── [auth components]
│   │   ├── onboarding/             # User onboarding
│   │   │   └── [onboarding pages]
│   │   ├── portal/                 # Client portal pages
│   │   │   └── [portal_id]/
│   │   ├── privacy/                # Privacy policy
│   │   ├── survey/                 # Survey pages
│   │   │   └── [surveyId]/
│   │   ├── terms/                  # Terms of service
│   │   ├── test/                   # Test pages
│   │   ├── favicon.ico
│   │   ├── globals.css             # Global styles
│   │   ├── layout.tsx              # Root layout
│   │   ├── page.tsx                # Home page
│   │   └── providers.tsx           # Context providers
│   ├── components/                 # React Components
│   │   ├── AuthGuard.tsx           # Authentication guard
│   │   ├── client-intake/          # Client intake components
│   │   │   ├── ClientImport.tsx
│   │   │   ├── ClientList.tsx
│   │   │   └── ClientProfile.tsx
│   │   ├── conversation/           # Conversation components
│   │   │   ├── ConversationList.tsx
│   │   │   ├── ConversationView.tsx
│   │   │   ├── MessageComposer.tsx
│   │   │   ├── MessageList.tsx
│   │   │   ├── RecommendationActions.tsx
│   │   │   └── [additional components]
│   │   ├── modals/                 # Modal components
│   │   │   ├── CampaignModal.tsx
│   │   │   ├── ClientModal.tsx
│   │   │   ├── ConfirmModal.tsx
│   │   │   ├── MessageModal.tsx
│   │   │   ├── PortalModal.tsx
│   │   │   └── SurveyModal.tsx
│   │   ├── nudges/                 # Nudge components
│   │   │   ├── NudgeCard.tsx
│   │   │   ├── NudgeList.tsx
│   │   │   ├── NudgePreview.tsx
│   │   │   ├── NudgeScheduler.tsx
│   │   │   └── NudgeStats.tsx
│   │   ├── onboarding/             # Onboarding components
│   │   │   ├── OnboardingFlow.tsx
│   │   │   └── OnboardingStep.tsx
│   │   ├── profile/                # Profile components
│   │   │   ├── ProfileForm.tsx
│   │   │   ├── ProfileSettings.tsx
│   │   │   └── ProfileStats.tsx
│   │   ├── settings/               # Settings components
│   │   │   └── SettingsPanel.tsx
│   │   ├── survey/                 # Survey components
│   │   │   ├── ClientIntakeSurvey.tsx
│   │   │   ├── SurveyBuilder.tsx
│   │   │   ├── SurveyPreview.tsx
│   │   │   └── SurveyResults.tsx
│   │   ├── ui/                     # UI components
│   │   │   ├── Button.tsx
│   │   │   ├── Card.tsx
│   │   │   ├── Input.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── TagFilter.tsx
│   │   │   └── [additional UI components]
│   │   ├── ThemeProvider.tsx       # Theme provider
│   │   └── ThemeSwitcher.tsx       # Theme switcher
│   ├── context/                    # React Context
│   │   ├── AppContext.tsx          # Main app context
│   │   └── SidebarContext.tsx      # Sidebar context
│   ├── utils/                      # Utility functions
│   │   ├── theme.ts                # Theme utilities
│   │   ├── timezone.test.ts        # Timezone tests
│   │   └── timezone.ts             # Timezone utilities
│   ├── public/                     # Static assets
│   │   ├── AI Nudge Logo.png
│   │   ├── file.svg
│   │   ├── globe.svg
│   │   ├── google2b88652066896ead.html
│   │   ├── logo.svg
│   │   ├── next.svg
│   │   ├── vercel.svg
│   │   └── window.svg
│   ├── Dockerfile                  # Docker configuration
│   ├── eslint.config.mjs           # ESLint configuration
│   ├── next-env.d.ts               # Next.js type definitions
│   ├── next.config.js              # Next.js configuration
│   ├── package-lock.json           # NPM lock file
│   ├── package.json                # NPM dependencies
│   ├── postcss.config.js           # PostCSS configuration
│   ├── README.md
│   ├── tailwind.config.js          # Tailwind CSS configuration
│   ├── THEME_GUIDE.md              # Theme documentation
│   ├── tsconfig.json               # TypeScript configuration
│   └── tsconfig.tsbuildinfo        # TypeScript build info
├── node_modules/                   # NPM dependencies
├── package-lock.json               # Root package lock file
├── package.json                    # Root package.json
├── production.env                  # Production environment
├── pytest.ini                     # Pytest configuration
├── render-build.sh                 # Render deployment script
├── render.yaml                     # Render configuration
├── spec.md                         # Project specification (this file)
├── venv/                          # Python virtual environment
└── [additional root files]
```

### **Key Architecture Components**

#### **Backend Architecture**
- **FastAPI Framework:** Modern, fast Python web framework
- **SQLModel ORM:** Type-safe database operations with Pydantic integration
- **PostgreSQL Database:** Robust relational database with JSON support
- **Redis + Celery:** Asynchronous task processing and caching
- **Alembic Migrations:** Database schema version control

#### **Frontend Architecture**
- **Next.js 14:** React framework with App Router
- **TypeScript:** Type-safe JavaScript development
- **Tailwind CSS:** Utility-first CSS framework
- **Framer Motion:** Animation and interaction library
- **React Context:** State management without external libraries

#### **AI & ML Integration**
- **OpenAI API:** GPT models for text generation and analysis
- **Google Generative AI:** Gemini models for additional AI capabilities
- **Vector Search:** Semantic search and similarity matching
- **Embedding Generation:** Text embedding for content matching

#### **External Integrations**
- **Twilio:** SMS and voice communication
- **Google OAuth:** Authentication and contact import
- **MLS APIs:** Real estate data integration (FlexMLS, RESO)
- **Redis:** Caching and session management

---

## **Development Workflow**

### **Environment Setup**
1. **Clone Repository:** `git clone <repository-url>`
2. **Backend Setup:**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   cp .env.example .env  # Configure environment variables
   ```
3. **Frontend Setup:**
   ```bash
   cd frontend
   npm install
   ```
4. **Database Setup:**
   ```bash
   # Using Docker Compose
   docker-compose up -d db redis
   ```
5. **Start Development:**
   ```bash
   # Backend
   cd backend && uvicorn api.main:app --reload --port 8001
   
   # Frontend
   cd frontend && npm run dev
   ```

### **Testing Strategy**
- **Unit Tests:** Pytest for backend
- **Integration Tests:** API endpoint testing with FastAPI TestClient
- **Manual Testing:** Comprehensive test scenarios for each feature
- **Content Recommendation Testing:**
  - Test content resource creation and management
  - Verify client matching logic with various tag combinations
  - Test AI message generation for content sharing
  - Validate integration with AI suggestions interface
  - Test multi-vertical content recommendation functionality

### **Deployment Pipeline**
- **Development:** Local Docker Compose environment
- **Staging:** Render.com backend + Vercel frontend
- **Production:** Automated deployment with environment-specific configurations

---

## **Business Logic & Data Flow**

### **Event Processing Pipeline**
1. **Event Detection:** External integrations detect market/relationship events
2. **Event Classification:** AI categorizes events by type and relevance
3. **Audience Identification:** System finds clients affected by the event
4. **Campaign Generation:** AI creates strategic campaign briefings
5. **Owner Review:** Human approval and refinement workflow
6. **Execution:** Multi-channel message delivery
7. **Response Tracking:** Monitor engagement and outcomes
8. **Learning:** Update AI models based on results

### **Client Intelligence Engine**
- **Data Sources:** CRM data, communication history, external integrations
- **Profiling:** AI analysis of client preferences and behavior patterns
- **Segmentation:** Dynamic client grouping based on characteristics
- **Recommendations:** Personalized engagement suggestions

### **Campaign Management**
- **Briefing Creation:** AI-generated campaign strategies
- **Message Drafting:** Personalized message content generation
- **Audience Targeting:** Intelligent client selection
- **Scheduling:** Optimal timing recommendations
- **Execution:** Multi-channel delivery with tracking
- **Analytics:** Performance measurement and optimization

### **Content Recommendation Engine**
- **Resource Management:** Business owners add content resources with categories and metadata
- **Client Profiling:** System analyzes client tags (user-set and AI-generated) for interests and needs
- **Matching Algorithm:** Content resources are matched to clients based on category/tag overlap
- **AI Message Generation:** Personalized messages are generated for each client-resource match
- **Integration with AI Suggestions:** Content recommendations are converted to campaign briefings and appear in the unified AI suggestions interface
- **Usage Analytics:** System tracks which content resources are shared and their engagement rates
- **Multi-Vertical Adaptability:** Content recommendation logic works across all business verticals

### **Survey Processing Pipeline**
1. **Survey Trigger:** System automatically sends intake surveys to new clients or agents manually trigger surveys
2. **Response Collection:** Clients complete multi-step surveys via SMS or web interface
3. **AI Processing:** Survey responses are processed by AI to extract preferences and generate client tags
4. **Client Profiling Update:** Extracted data updates the client's profile and preferences
5. **Matching Enhancement:** Updated client profile improves property/content matching accuracy
6. **Portal Generation:** Enhanced client profiles enable better curated portal content

### **Portal Generation Pipeline**
1. **Match Curation:** AI finds and scores property matches for each client
2. **Portal Creation:** System generates secure portal links with curated property matches
3. **Client Access:** Clients access portals via secure, shareable links
4. **Feedback Collection:** Clients provide feedback on properties through the portal interface
5. **Agent Notification:** Agents receive real-time updates on client feedback and engagement
6. **Continuous Improvement:** Client feedback improves future matching and portal curation

### **Advanced Workflow Engine**
- **Conversational Playbooks:** Industry-specific conversation flows with configurable steps
- **Relationship Planning:** Automated relationship nurturing sequences with timing controls
- **Event Processing Pipeline:** Real-time event detection and intelligent response generation
- **Campaign Automation:** End-to-end campaign lifecycle management
- **Vertical-Specific Workflows:**
  - **Real Estate:** MLS integration, property alerts, market updates, buyer/seller workflows
  - **Therapy:** HIPAA-compliant workflows, appointment reminders, wellness check-ins
  - **Extensible Framework:** Easy addition of new business verticals through pluggable modules
- **Playbook Types:**
  - **Long-term Nurture:** Ongoing relationship building with configurable intervals
  - **Short-term Lead Conversion:** Immediate engagement strategies for new prospects
  - **Personal Event Reminders:** Birthday, anniversary, holiday, and milestone messages
  - **Custom Frequency Playbooks:** User-defined engagement schedules and triggers
  - **Event-Driven Workflows:** Automated responses to market events and client actions
- **Workflow Components:**
  - **Actions:** Reusable workflow actions for common tasks
  - **Triggers:** Event-driven workflow initiation
  - **Conditions:** Smart decision points in workflow execution
  - **Timing Controls:** Sophisticated scheduling and delay mechanisms
  - **Personalization:** Dynamic content adaptation based on client profile

---

## **Security & Compliance**

### **Authentication & Authorization**
- **JWT Tokens:** Secure token-based authentication
- **OAuth Integration:** Google OAuth for contact import
- **Role-based Access:** User type-specific permissions
- **Session Management:** Secure session handling

### **Data Protection**
- **Encryption:** Data encryption in transit and at rest
- **HIPAA Compliance:** Healthcare-specific data protection (therapy vertical)
- **GDPR Compliance:** User data privacy and control
- **Audit Logging:** Comprehensive activity tracking

### **API Security**
- **Rate Limiting:** Protection against abuse
- **Input Validation:** Comprehensive request validation
- **CORS Configuration:** Secure cross-origin resource sharing
- **Error Handling:** Secure error responses without information leakage

---

## **Monitoring & Observability**

### **Logging Strategy**
- **Structured Logging:** JSON-formatted logs with consistent fields
- **Log Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Context Enrichment:** Request IDs, user context, performance metrics
- **Centralized Collection:** Log aggregation and analysis

### **Performance Monitoring**
- **Response Times:** API endpoint performance tracking
- **Database Queries:** Query performance and optimization
- **External API Calls:** Third-party service monitoring
- **Resource Utilization:** CPU, memory, and disk usage

### **Error Tracking**
- **Exception Handling:** Comprehensive error capture
- **Stack Traces:** Detailed error information for debugging
- **Alerting:** Automated notifications for critical issues
- **Error Recovery:** Graceful degradation and retry mechanisms

---

## **Future Roadmap**

### **Short-term (Next 3 Months)**
- **Enhanced AI Capabilities:** Improved message generation and personalization
- **Additional Integrations:** More MLS providers and business tools
- **Mobile App:** Native mobile application development
- **Advanced Analytics:** Detailed performance dashboards

### **Medium-term (3-6 Months)**
- **Multi-tenant Architecture:** Support for multiple organizations
- **Advanced Workflows:** Complex automation and decision trees
- **API Ecosystem:** Public API for third-party integrations
- **Machine Learning Pipeline:** Automated model training and deployment

### **Long-term (6+ Months)**
- **Predictive Analytics:** Advanced forecasting and trend analysis
- **Voice Integration:** Voice-based interactions and responses
- **Global Expansion:** Multi-language and multi-region support
- **Enterprise Features:** Advanced security and compliance features

---

## **Success Metrics**

### **User Engagement**
- **Daily Active Users:** User retention and engagement
- **Campaign Performance:** Message open rates and response rates
- **Feature Adoption:** Usage of key features and capabilities
- **User Satisfaction:** Feedback and satisfaction scores

### **Business Impact**
- **Revenue Generation:** Direct impact on user business outcomes
- **Time Savings:** Efficiency gains for users
- **Relationship Strength:** Measurable improvement in client relationships
- **Market Expansion:** Growth into new verticals and markets

### **Technical Performance**
- **System Reliability:** Uptime and error rates
- **Response Times:** API and UI performance
- **Scalability:** System capacity and growth readiness
- **Security:** Security incident prevention and response


## **🔒 Development Guidelines**

### **No Silent Deletions**  
Never remove logic, data fields, or existing behavior without explicitly asking for approval and confirming its impact.

### **📈 Built-In Observability**  
Every new block of code must include meaningful logging, inline comments explaining intent, and visibility into critical paths.

### **🧪 Testability First**  
Every feature or change must include a short, clear **"How to Test"** section—covering expected behavior, edge cases, and success/failure signals.

### **Full File Mandate**  
Always deliver the complete, full-text code for any requested file. Start with the entire file and apply only the necessary changes. No partial code, snippets, or patches.

### **Surgical Changes Only**  
Only apply minimal and specific changes that have been previously aligned on. No new features, logic, or style preferences that weren't part of the explicit plan.

### **Pre-Delivery Verification**  
Before providing code, perform a final check to ensure all original, untouched functions have been preserved and that the final file is complete and correct.

---

---

This specification serves as the comprehensive guide for the AI Nudge project, ensuring all development aligns with the product vision, technical architecture, and business objectives while maintaining the highest standards of code quality and user experience. 