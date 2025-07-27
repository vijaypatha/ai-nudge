# AI Nudge Backend

## Environment Setup

### Required Environment Variables

Copy the example environment file and configure your API keys:

```bash
cp .env.example .env
```

### API Keys Required

#### OpenAI API Key
- **Purpose**: Text embeddings and AI completions
- **Get it**: https://platform.openai.com/account/api-keys
- **Format**: `sk-...`

#### Google API Key
- **Purpose**: Google Search integration
- **Get it**: https://console.cloud.google.com/apis/credentials
- **Format**: `AIza...`

#### Google Custom Search Engine ID
- **Purpose**: Web search functionality
- **Get it**: https://programmablesearchengine.google.com/
- **Format**: `012345678901234567890:abcdefghijk`

#### Twilio Credentials
- **Purpose**: SMS messaging and phone verification
- **Get it**: https://console.twilio.com/
- **Required**: Account SID, Auth Token, Phone Number, Verify Service SID

### Environment Validation

The application will validate your environment on startup and provide clear error messages for:
- Missing required variables
- Placeholder values that need to be replaced
- Invalid API key formats

### Example .env Configuration

```env
# OpenAI
OPENAI_API_KEY=sk-your-actual-openai-api-key-here

# Google
GOOGLE_API_KEY=AIza-your-actual-google-api-key-here
GOOGLE_CSE_ID=012345678901234567890:abcdefghijk

# Twilio
TWILIO_ACCOUNT_SID=AC-your-actual-account-sid-here
TWILIO_AUTH_TOKEN=your-actual-auth-token-here
TWILIO_PHONE_NUMBER=+1234567890
TWILIO_VERIFY_SERVICE_SID=VA-your-actual-verify-service-sid-here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_nudge

# Application
SECRET_KEY=your-actual-secret-key-here
MLS_PROVIDER=flexmls
SPARK_API_DEMO_TOKEN=your-actual-spark-token-here
RESO_API_BASE_URL=https://api.flexmls.com
RESO_API_TOKEN=your-actual-reso-token-here

# OAuth
GOOGLE_CLIENT_ID=your-actual-google-client-id-here
GOOGLE_CLIENT_SECRET=your-actual-google-client-secret-here
GOOGLE_REDIRECT_URI=http://localhost:3000/auth/callback/google
```

## Running the Application

### Development
```bash
docker-compose up
```

### Production
```bash
docker-compose -f docker-compose.prod.yml up
```

## Troubleshooting

### Common Issues

1. **"Incorrect API key provided"**
   - Ensure you've replaced placeholder values in `.env`
   - Verify API keys are valid and have proper permissions

2. **"Missing required environment variables"**
   - Check that all required variables are set in `.env`
   - Ensure no variables are empty or contain placeholder text

3. **Database connection errors**
   - Verify `DATABASE_URL` is correct
   - Ensure PostgreSQL is running and accessible

### Getting API Keys

#### OpenAI
1. Go to https://platform.openai.com/account/api-keys
2. Create a new API key
3. Copy the key (starts with `sk-`)

#### Google
1. Go to https://console.cloud.google.com/
2. Create a new project or select existing
3. Enable the Custom Search API
4. Create credentials (API Key)
5. For Custom Search Engine ID, go to https://programmablesearchengine.google.com/

#### Twilio
1. Sign up at https://www.twilio.com/
2. Get Account SID and Auth Token from console
3. Purchase a phone number
4. Create a Verify service for OTP functionality 