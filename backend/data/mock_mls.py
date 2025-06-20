from typing import List
from .models import Property, Client
from datetime import datetime # Not used in current mocks, but good for future extension

def get_mock_properties() -> List[Property]:
    return [
        Property(id="prop-A101", address="101 Elm Street, Springfield, IL", price=350000.00, bedrooms=3, bathrooms=2.0, sqft=1750, image_url="https://via.placeholder.com/350x250.png?text=101+Elm+St", description="Charming colonial with a large, fenced backyard and updated kitchen."),
        Property(id="prop-B202", address="202 Oak Avenue, Shelbyville, OH", price=475000.00, bedrooms=4, bathrooms=2.5, sqft=2200, image_url="https://via.placeholder.com/350x250.png?text=202+Oak+Ave", description="Spacious modern home featuring an open floor plan, gourmet kitchen."),
        Property(id="prop-C303", address="303 Maple Drive, Capital City, CA", price=620000.00, bedrooms=5, bathrooms=3.5, sqft=3100, image_url="https://via.placeholder.com/350x250.png?text=303+Maple+Dr", description="Luxurious estate with a private pool and stunning panoramic views."),
        Property(id="prop-D404", address="404 Pine Lane, Ogdenville, NV", price=280000.00, bedrooms=2, bathrooms=1.0, sqft=1100, image_url="https://via.placeholder.com/350x250.png?text=404+Pine+Ln", description="Cozy, well-maintained bungalow perfect for first-time homebuyers."),
        Property(id="prop-E505", address="505 Cedar Crest, North Haverbrook, TX", price=710000.00, bedrooms=4, bathrooms=3.0, sqft=2800, image_url="https://via.placeholder.com/350x250.png?text=505+Cedar+Crest", description="Beautiful two-story home in a desirable neighborhood, with a large bonus room."),
    ]

def get_mock_clients() -> List[Client]:
    return [
        Client(id="client-001", name="Alice Wonderland", email="alice.w@example.com", phone="555-0101", notes="Interested in properties with gardens. Budget around $400k."),
        Client(id="client-002", name="Bob The Builder", email="bob.b@example.com", phone="555-0102", notes="Looking for a fixer-upper or something with a large workshop. Needs at least 3 bedrooms."),
        Client(id="client-003", name="Charlie Chaplin", email="charlie.c@example.com", phone="555-0103", notes="Needs a pet-friendly place (has two dogs), preferably single-story. Likes quiet neighborhoods."),
        Client(id="client-004", name="Diana Prince", email="diana.p@example.com", phone="555-0104", notes="Relocating for a new job. Needs good access to downtown. Interested in modern condos."),
        Client(id="client-005", name="Edward Scissorhands", email="edward.s@example.com", phone="555-0105", notes="Looking for unique properties, possibly with large, mature landscaping."),
    ]
