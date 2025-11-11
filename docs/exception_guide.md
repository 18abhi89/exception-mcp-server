## Exception Investigation Guide

### OUT_OF_ORDER Exception
- **Cause**: Event received out of sequence
- **Common patterns**: CANCEL before NEW, higher version before lower
- **Resolution**: Check audit table for base event

### INVALID_EVENT Exception  
- **Cause**: Unsupported event type received
- **Common patterns**: Upstream schema changes, configuration drift
- **Resolution**: Verify event type against supported list

### PREVIOUSLY_PROCESSED_MESSAGE Exception
- **Cause**: Duplicate event_id detected
- **Common patterns**: Kafka replay, upstream retry logic
- **Resolution**: Verify idempotency handling

### Investigation Steps
1. Query exception by exception_id
2. Check audit history for same event_id
3. Look for patterns in last 24h
4. Check times_replayed for chronic failures
