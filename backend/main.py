from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Import routers
from api.rest import campaigns, inbox
# Placeholder for other potential routers
# from api.webhooks import some_webhook_router

app = FastAPI(
    title="AI Nudge API",
    version="0.1.0",
    description="API for AI Nudge CRM",
)

# CORS (Cross-Origin Resource Sharing)
origins = [
    "http://localhost:3000",  # Frontend local development
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
# These will be created in subsequent steps, so this might show errors if run standalone now
# For now, we are just setting up the structure.
# Ensure these files exist before running the app.
app.include_router(campaigns.router, prefix="/campaigns", tags=["Campaigns"])
app.include_router(inbox.router, prefix="/inbox", tags=["Inbox"])
# app.include_router(some_webhook_router.router, prefix="/webhooks", tags=["Webhooks"])


@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to AI Nudge API"}

# To simulate OpenAI key presence for llm_client
os.environ.setdefault("OPENAI_API_KEY", "mock_openai_key_if_not_set_in_env")

if __name__ == "__main__":
    import uvicorn
    # This part is for local execution without Uvicorn CLI directly, not typically used in Docker with CMD
    # uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
    pass # Docker CMD will run the app
