#!/bin/bash

# A script to run a full end-to-end test on the AI Nudge API.

echo "--- [STEP 1] Health Check & Initial State ---"
curl -s http://localhost:8001/
PROPERTY_ID=$(curl -s http://localhost:8001/properties/ | jq -r '.[0].id')
echo "\n===> Captured Property ID: $PROPERTY_ID"
echo "\n"


echo "--- [STEP 2] Create a PERFECT MATCH Client ---"

# The -L flag automatically follows the 307 redirect.
# FIX: Client preferences now match the seeded property to guarantee a nudge.
CLIENT_JSON=$(curl -s -L -X POST http://localhost:8001/clients/ \
-H "Content-Type: application/json" \
-d '{
  "full_name": "Perfect Match Client",
  "email": "perfect.match@test.com",
  "phone": "+18005553000",
  "tags": ["buyer", "has_preapproval"],
  "preferences": {
    "locations": ["Sunnyvale"],
    "budget_max": 900000,
    "min_bedrooms": 3,
    "notes": [
      "Wants a move-in ready home."
    ]
  }
}')

echo "Client Created JSON Response:"
echo $CLIENT_JSON

CLIENT_ID=$(echo $CLIENT_JSON | jq -r .id)
echo "\n===> Captured Client ID: $CLIENT_ID"

echo "\n(Waiting 2 seconds for background task to run...)"
sleep 2

echo "\nVerifying scheduled messages for new client..."
curl -s http://localhost:8001/clients/$CLIENT_ID/scheduled-messages
echo "\n"


echo "--- [STEP 3] Simulate Price Drop & Check for Nudge ---"
echo "\nSimulating price drop..."
# Price is dropped to 700k, which is under the client's 900k budget.
curl -s -X POST http://localhost:8001/properties/$PROPERTY_ID/simulate-price-drop \
-H "Content-Type: application/json" \
-d '{"new_price": 700000}'

echo "\n\n(Waiting 2 seconds for nudge engine to process...)"
sleep 2

echo "\nChecking /nudges endpoint for new campaign..."
curl -s -L http://localhost:8001/nudges/
echo "\n\n--- TEST COMPLETE ---"