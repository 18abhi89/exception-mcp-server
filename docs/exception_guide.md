## Exception Investigation Guide

This guide helps investigate trade ingestion and consumer exceptions across the trading platform.

## Exception Categories

### SEQUENCING Exceptions

#### OUT_OF_ORDER
- **Cause**: Events received out of sequence
- **Common patterns**:
  - CANCEL before NEW event
  - MODIFY before base NEW event
  - DELETE on non-existent trade
  - Version gaps (v3 before v2)
- **Why retries fail**: The dependent event may not have arrived yet
- **Resolution**:
  - Check audit table for base event
  - Implement temporal parking (wait 2-5 minutes)
  - Consider message ordering guarantees in Kafka
  - Check partition key strategy

### VALIDATION Exceptions

#### INVALID_EVENT
- **Cause**: Schema or data validation failures
- **Common patterns**:
  - Unsupported event types
  - Missing required fields
  - Null/empty critical fields
  - Schema violations
- **Why retries fail**: Data issue won't fix itself
- **Resolution**:
  - Verify event type against supported list
  - Check schema version compatibility
  - Validate upstream system configuration
  - Review field mapping logic

### DUPLICATE Exceptions

#### PREVIOUSLY_PROCESSED_MESSAGE
- **Cause**: Duplicate event_id detected
- **Common patterns**:
  - Kafka consumer group rebalancing
  - Upstream retry logic
  - Network issues causing replays
- **Why retries fail**: Idempotency check will keep failing
- **Resolution**:
  - Verify idempotency key implementation
  - Check consumer offset management
  - Review duplicate detection logic
  - Consider unique constraints

### BUSINESS_LOGIC Exceptions

#### CALCULATION_ERROR
- **Cause**: Business rule or calculation failures
- **Common patterns**:
  - Settlement date calculation errors
  - Holiday calendar issues
  - Invalid business days
  - Reference data missing
- **Why retries fail**: Reference data or configuration issue
- **Resolution**:
  - Update holiday calendar
  - Verify reference data availability
  - Check business rule configuration
  - Review calculation logic

### INFRASTRUCTURE Exceptions

#### TIMEOUT
- **Cause**: Downstream service timeouts
- **Common patterns**:
  - Network latency
  - Service overload
  - Database connection issues
- **Why retries fail**: Underlying infrastructure issue persists
- **Resolution**:
  - Check service health
  - Review timeout configuration
  - Implement circuit breakers
  - Consider async processing

## Investigation Steps

### 1. High Retry Count (> 5)
If an exception has been retried more than 5 times:
- **STOP retrying immediately** - it won't magically fix itself
- Investigate root cause using similar historical cases
- Check if it's a category that benefits from retries (SEQUENCING might, VALIDATION won't)

### 2. Query Exception Details
```
Use tool: getHighRetryExceptions with threshold=5
```

### 3. Find Similar Historical Cases
```
Use tool: findSimilarExceptions with error_message
```

### 4. Analyze Specific Exception
```
Use tool: analyzeException with exception_id
```

### 5. Check System Context
- Source system (ATLAS vs trade-ingestion-service)
- Raising system (which service caught it)
- Event type and version
- Timestamp patterns

## When to Stop Retrying

**Immediate stop for:**
- VALIDATION errors (data/schema issues)
- BUSINESS_LOGIC errors (configuration issues)
- DUPLICATE errors (idempotency checks)

**May benefit from retries:**
- SEQUENCING errors (if within grace period)
- INFRASTRUCTURE errors (if transient)

**Maximum retry threshold: 5**
- After 5 retries, manual intervention needed
- Check historical resolutions for similar cases
