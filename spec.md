# AI Nudge - Project Specification

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
- **Authentication:** JWT with OAuth2 (Google, Microsoft)
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
- **`rest/`:** REST API endpoints organized by domain
- **`security.py`:** JWT authentication and user management
- **`websocket_manager.py`:** Real-time communication handling

#### **Agent Core (`/agent_core/`)**
- **`brain/`:** AI decision-making and reasoning engine
- **`agents/`:** Specialized AI agents for different tasks
- **`orchestrator.py`:** Coordinates between different AI components
- **`audience_builder.py`:** Client targeting and segmentation

#### **Data Layer (`/data/`)**
- **`models/`:** SQLModel database models
- **`database.py`:** Database connection and session management
- **`crm.py`:** Customer relationship management operations
- **`vector.py`:** Vector search and similarity matching

#### **Integrations (`/integrations/`)**
- **`mls/`:** Multiple Listing Service integrations
- **`twilio_*.py`:** SMS/voice communication
- **`oauth/`:** Google and Microsoft OAuth
- **`openai.py`:** AI model integration

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
- **Contact Import:** Google/Microsoft OAuth integration for contact import
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

### **5. Personalization & Learning**
- **Style Adaptation:** AI learns from user message edits
- **Behavior Profiling:** User interaction pattern analysis
- **Performance Optimization:** Continuous improvement based on outcomes

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
- **Unit Tests:** Pytest for backend, Jest for frontend
- **Integration Tests:** API endpoint testing with FastAPI TestClient
- **E2E Tests:** Playwright for critical user flows
- **Manual Testing:** Comprehensive test scenarios for each feature

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

---

## **Security & Compliance**

### **Authentication & Authorization**
- **JWT Tokens:** Secure token-based authentication
- **OAuth Integration:** Google and Microsoft OAuth for contact import
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