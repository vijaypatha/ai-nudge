# # backend/api/main.py

# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# # --- NEW IMPORT ---
# from fastapi.routing import APIRoute # Import APIRoute for type hinting

# from backend.api.rest import clients
# from backend.api.rest import properties
# from backend.api.rest import campaigns
# from backend.api.rest import inbox

# # Initialize the FastAPI app
# app = FastAPI(
#     title="AI Nudge Backend API",
#     description="The core API for the AI Nudge intelligent assistant.",
#     version="0.1.0",
# )

# # Configure CORS middleware
# origins = [
#     "http://localhost:3000",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include all routers in the main FastAPI application.
# app.include_router(clients.router)
# app.include_router(properties.router)
# app.include_router(campaigns.router)
# app.include_router(inbox.router)

# @app.get("/")
# async def read_root():
#     """
#     Root endpoint for the AI Nudge API.
#     """
#     return {"message": "Welcome to AI Nudge Backend API!"}

# # --- NEW DIAGNOSTIC ENDPOINT ---
# @app.get("/_debug/routes", response_model=list[dict])
# async def debug_list_routes():
#     """
#     Debugging endpoint to list all registered API routes.
#     How it works for the robot: This is like asking the "Reception Desk Manager"
#     to print out its internal list of all the "buttons" it knows it has.
#     """
#     routes_list = []
#     # Iterate through all routes registered with the FastAPI application.
#     for route in app.routes:
#         # Check if the route is an instance of APIRoute (which is what our @app.get/@app.post creates).
#         if isinstance(route, APIRoute):
#             routes_list.append({
#                 "path": route.path,        # The URL path of the route
#                 "name": route.name,        # The internal name of the route
#                 "methods": route.methods,  # The HTTP methods supported by the route (GET, POST, etc.)
#                 "endpoint": route.endpoint.__name__ # The name of the Python function handling the route
#             })
#     print("\n--- DEBUG: FASTAPI REGISTERED ROUTES ---")
#     for r in routes_list:
#         print(f"Path: {r['path']}, Methods: {r['methods']}")
#     print("-----------------------------------------")
#     return routes_list


# backend/api/main.py
# This is a temporary, minimal FastAPI app for Docker testing.

from fastapi import FastAPI

# Initialize a very basic FastAPI app.
app = FastAPI(title="Docker Test API")

# Define a simple root endpoint.
@app.get("/")
async def read_root():
    """
    Returns a simple message to confirm the API is running inside Docker.
    """
    return {"message": "Hello from Dockerized FastAPI!"}