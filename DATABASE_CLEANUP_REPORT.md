# Database Cleanup Report
*Generated on: $(date)*

## Executive Summary

Based on the automated analysis of your AI Nudge application, here are the key findings:

### **Fields Safe to Remove**
The following fields appear to be unused or have minimal usage and can be safely removed:

1. **`mls_username`** - Only 4 references (model definition + migration)
2. **`mls_password`** - Only 4 references (model definition + migration)  
3. **`license_number`** - Only 4 references (model definition + migration)

### **Fields with Low Usage**
These fields have very low usage and should be reviewed:

1. **`faq_auto_responder_enabled`** - Only 2 references
2. **`processed_at`** - Only 2 references

## Detailed Analysis

### 1. Model Field Analysis

**Total Tables Analyzed**: 8
- user
- event  
- feedback
- client
- resource
- message
- campaign
- faq

### 2. Field Usage Statistics

**Most Used Fields** (Top 10):
1. `v` - 4,607 references
2. `id` - 3,728 references  
3. `type` - 3,066 references
4. `source` - 1,964 references
5. `url` - 1,285 references
6. `user` - 1,272 references
7. `client` - 1,101 references
8. `content` - 881 references
9. `errors` - 861 references
10. `status` - 728 references

### 3. Specific Field Analysis

#### Fields You Mentioned:

**`mls_username`**
- **References**: 4
- **Locations**: 
  - `database_analysis.py` (analysis script)
  - `database_analysis_simple.py` (analysis script)
  - `data/models/user.py` (model definition)
  - `alembic/versions/357f39f135c0_add_explicit_tablename_to_.py` (migration)
- **Status**: SAFE TO REMOVE - Only exists in model and migration

**`mls_password`**
- **References**: 4
- **Locations**: Same as mls_username
- **Status**: SAFE TO REMOVE - Only exists in model and migration

**`license_number`**
- **References**: 4
- **Locations**: Same as above
- **Status**: SAFE TO REMOVE - Only exists in model and migration

### 4. Low Usage Fields

**`faq_auto_responder_enabled`**
- **References**: 2
- **Locations**:
  - `data/models/user.py` (model definition)
  - `alembic/versions/357f39f135c0_add_explicit_tablename_to_.py` (migration)
- **Recommendation**: REVIEW - May be used in business logic

**`processed_at`**
- **References**: 2
- **Locations**:
  - `data/models/event.py` (model definition)
  - `alembic/versions/357f39f135c0_add_explicit_tablename_to_.py` (migration)
- **Recommendation**: REVIEW - May be used in event processing

## Recommendations

### Immediate Actions (Safe to Remove)

1. **Remove `mls_username` field**
   - Create migration to drop column
   - Remove from user model
   - Update any related code

2. **Remove `mls_password` field**
   - Create migration to drop column
   - Remove from user model
   - Update any related code

3. **Remove `license_number` field**
   - Create migration to drop column
   - Remove from user model
   - Update any related code

### Review Required

1. **`faq_auto_responder_enabled`**
   - Check if this is used in FAQ auto-response logic
   - Review in `integrations/twilio_incoming.py` and `integrations/gemini.py`

2. **`processed_at`**
   - Check if this is used in event processing pipeline
   - Review in `workflow/pipeline.py` and related event processing

## Migration Strategy

### Step 1: Create Migration
```bash
# Create migration to remove unused fields
alembic revision --autogenerate -m "remove_unused_mls_fields"
```

### Step 2: Update Models
Remove the fields from the model definitions in `data/models/user.py`

### Step 3: Test
- Run tests to ensure no breaking changes
- Test in development environment
- Verify application functionality

### Step 4: Deploy
- Apply migration to production
- Monitor for any issues

## Code Locations to Update

### Files to Modify:
1. `data/models/user.py` - Remove field definitions
2. `alembic/versions/` - New migration file
3. Any test files that reference these fields

### Files to Review:
1. `integrations/twilio_incoming.py` - Check for `faq_auto_responder_enabled` usage
2. `workflow/pipeline.py` - Check for `processed_at` usage
3. `integrations/gemini.py` - Check for FAQ-related logic

## Risk Assessment

### Low Risk Fields (Safe to Remove)
- `mls_username` - No business logic usage
- `mls_password` - No business logic usage  
- `license_number` - No business logic usage

### Medium Risk Fields (Review Required)
- `faq_auto_responder_enabled` - May affect FAQ functionality
- `processed_at` - May affect event processing

## Next Steps

1. **Review the low-usage fields** to ensure they're not critical
2. **Create migration** for the safe-to-remove fields
3. **Update model definitions** to remove unused fields
4. **Test thoroughly** before applying to production
5. **Monitor** after deployment for any issues

## Files Generated

- `database_analysis_report.json` - Detailed analysis data
- `DATABASE_CLEANUP_REPORT.md` - This report

---

*This report was generated automatically by the database analysis script. Please review all recommendations before implementing changes.* 