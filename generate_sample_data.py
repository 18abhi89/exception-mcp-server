"""
Generate sample exception data for testing.

Creates 100 technical exceptions with overlapping method chains for good similarity search.
"""

import csv
import uuid
from datetime import datetime, timedelta
import random

# Common method chains (to create overlapping stacktraces)
METHOD_CHAINS = [
    [
        "com.trading.validation.TradeValidator.validate(TradeValidator.java:45)",
        "com.trading.service.TradeService.processTrade(TradeService.java:67)",
        "com.trading.kafka.MessageHandler.handleMessage(MessageHandler.java:34)",
        "com.trading.kafka.KafkaConsumer.poll(KafkaConsumer.java:89)"
    ],
    [
        "com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:197)",
        "com.trading.repository.TradeRepository.findById(TradeRepository.java:45)",
        "com.trading.service.TradeService.getTrade(TradeService.java:89)",
        "com.trading.controller.TradeController.getTradeById(TradeController.java:34)"
    ],
    [
        "com.trading.kafka.ProducerService.publishTrade(ProducerService.java:45)",
        "com.trading.service.TradePublisher.publish(TradePublisher.java:23)",
        "com.trading.async.AsyncProcessor.process(AsyncProcessor.java:67)"
    ],
    [
        "com.trading.parser.TradeFieldParser.parseFields(TradeFieldParser.java:78)",
        "com.trading.service.TradeIngestionService.ingest(TradeIngestionService.java:45)",
        "com.trading.kafka.MessageDeserializer.deserialize(MessageDeserializer.java:67)"
    ],
    [
        "redis.clients.jedis.Connection.connect(Connection.java:89)",
        "com.trading.cache.RedisCacheService.get(RedisCacheService.java:34)",
        "com.trading.service.ReferenceDataService.getSecurityInfo(ReferenceDataService.java:56)"
    ],
    [
        "com.trading.transformer.TradeTransformer.transform(TradeTransformer.java:89)",
        "com.trading.service.TradeService.transformTrade(TradeService.java:123)",
        "com.trading.processor.TradeProcessor.process(TradeProcessor.java:45)"
    ]
]

# Exception templates
EXCEPTION_TEMPLATES = [
    {
        "exception_type": "java.lang.NullPointerException",
        "category": "VALIDATION",
        "sub_category": "NULL_VALUE",
        "error_templates": [
            "Cannot invoke {} on null object",
            "Null pointer accessing field {}",
            "Object reference not set for {}"
        ],
        "chain_index": 0,
        "remarks_templates": [
            "Added null check before accessing {}. Reject message if object is null.",
            "Fixed by validating {} is not null before processing.",
            "Added defensive null checks in {} validation."
        ]
    },
    {
        "exception_type": "java.sql.SQLTimeoutException",
        "category": "INFRASTRUCTURE",
        "sub_category": "TIMEOUT",
        "error_templates": [
            "Connection to database timed out after {}ms",
            "Query execution exceeded timeout of {}ms",
            "Database connection timeout: {}ms"
        ],
        "chain_index": 1,
        "remarks_templates": [
            "Increased connection pool size from {} to {} and timeout to {}ms.",
            "Optimized query performance. Reduced execution time from {}ms to {}ms.",
            "Added connection pooling and increased timeout to {}ms."
        ]
    },
    {
        "exception_type": "org.apache.kafka.common.errors.TimeoutException",
        "category": "INFRASTRUCTURE",
        "sub_category": "NETWORK",
        "error_templates": [
            "Failed to update metadata after {} ms",
            "Kafka broker not available - timeout after {}ms",
            "Producer request timeout after {}ms"
        ],
        "chain_index": 2,
        "remarks_templates": [
            "Kafka cluster was down. Restarted brokers and added monitoring alerts.",
            "Increased producer timeout from {}ms to {}ms.",
            "Fixed network connectivity issue between services and Kafka brokers."
        ]
    },
    {
        "exception_type": "com.fasterxml.jackson.core.JsonParseException",
        "category": "VALIDATION",
        "sub_category": "INVALID_FORMAT",
        "error_templates": [
            "Unexpected character at position {}",
            "Cannot deserialize JSON - unexpected token",
            "Malformed JSON at line {}"
        ],
        "chain_index": 3,
        "remarks_templates": [
            "Upstream system sending malformed JSON. Fixed producer schema validation.",
            "Added JSON schema validation on consumer side. Reject invalid messages.",
            "Updated parser to handle additional JSON formats from upstream."
        ]
    },
    {
        "exception_type": "redis.clients.jedis.exceptions.JedisConnectionException",
        "category": "INFRASTRUCTURE",
        "sub_category": "CONNECTION_ERROR",
        "error_templates": [
            "Failed to connect to Redis on port {}",
            "Connection refused to Redis cache",
            "Redis connection timeout after {}ms"
        ],
        "chain_index": 4,
        "remarks_templates": [
            "Redis instance was not running. Started Redis and configured auto-restart.",
            "Increased Redis connection pool size from {} to {}.",
            "Fixed Redis connection configuration. Updated host from {} to {}."
        ]
    },
    {
        "exception_type": "java.lang.ArrayIndexOutOfBoundsException",
        "category": "VALIDATION",
        "sub_category": "INVALID_DATA",
        "error_templates": [
            "Index {} out of bounds for length {}",
            "Array index {} exceeds array size {}",
            "Attempting to access element {} in array of size {}"
        ],
        "chain_index": 3,
        "remarks_templates": [
            "Fixed bug in parser that assumed fixed number of fields. Added bounds checking.",
            "Added array length validation before access. Reject messages with insufficient fields.",
            "Updated parser to handle variable-length arrays from upstream."
        ]
    },
    {
        "exception_type": "java.lang.ClassCastException",
        "category": "VALIDATION",
        "sub_category": "TYPE_MISMATCH",
        "error_templates": [
            "Cannot cast {} to {}",
            "Class cast exception: {} cannot be converted to {}",
            "Type mismatch: expected {} but got {}"
        ],
        "chain_index": 5,
        "remarks_templates": [
            "Upstream changed field type. Updated parser to handle both types and convert.",
            "Added type checking before cast. Reject messages with incompatible types.",
            "Fixed type conversion in transformer. Now handles both {} and {}."
        ]
    },
    {
        "exception_type": "java.util.concurrent.RejectedExecutionException",
        "category": "INFRASTRUCTURE",
        "sub_category": "RESOURCE_EXHAUSTION",
        "error_templates": [
            "Task rejected from ThreadPoolExecutor",
            "Thread pool exhausted - cannot accept new tasks",
            "Executor queue capacity {} exceeded"
        ],
        "chain_index": 2,
        "remarks_templates": [
            "Increased thread pool size from {} to {} and added queue capacity monitoring.",
            "Implemented backpressure mechanism to slow down message consumption.",
            "Optimized async processing. Reduced thread pool utilization by {}%."
        ]
    },
    {
        "exception_type": "java.lang.OutOfMemoryError",
        "category": "INFRASTRUCTURE",
        "sub_category": "MEMORY",
        "error_templates": [
            "Java heap space exhausted",
            "OutOfMemoryError: unable to allocate {} bytes",
            "GC overhead limit exceeded"
        ],
        "chain_index": 3,
        "remarks_templates": [
            "Batch processor loading entire dataset into memory. Implemented streaming and increased heap from {}GB to {}GB.",
            "Memory leak in cache. Fixed cache eviction policy and increased heap to {}GB.",
            "Optimized object creation. Reduced memory usage by {}%."
        ]
    },
    {
        "exception_type": "org.postgresql.util.PSQLException",
        "category": "INFRASTRUCTURE",
        "sub_category": "DEADLOCK",
        "error_templates": [
            "ERROR: deadlock detected",
            "Database deadlock while acquiring lock on table {}",
            "Transaction deadlock - conflicting locks"
        ],
        "chain_index": 1,
        "remarks_templates": [
            "Reordered database lock acquisition to always lock tables in same order (trades then positions).",
            "Reduced transaction scope. Split large transaction into smaller batches.",
            "Added deadlock retry logic with exponential backoff."
        ]
    }
]

def generate_stacktrace(template, chain_index, error_message):
    """Generate stacktrace using method chain."""
    chain = METHOD_CHAINS[chain_index]
    exception_line = f"{template['exception_type']}: {error_message}"

    lines = [exception_line]
    for method in chain:
        lines.append(f"\tat {method}")

    # Sometimes add "... N more" at the end
    if random.random() > 0.5:
        lines.append(f"... {random.randint(5, 20)} more")

    return "\n".join(lines)

def generate_exceptions(count=100):
    """Generate exception records."""
    exceptions = []
    start_date = datetime.now() - timedelta(days=90)

    for i in range(count):
        template = random.choice(EXCEPTION_TEMPLATES)

        # Create exception record
        exception_id = str(uuid.uuid4())
        event_id = f"EVT-{i+1:04d}"
        created_date = start_date + timedelta(days=random.randint(0, 90), hours=random.randint(0, 23))

        # Generate error message
        error_template = random.choice(template['error_templates'])
        placeholder_count = error_template.count('{}')

        if placeholder_count == 0:
            error_message = error_template
        elif 'timeout' in error_template.lower() or 'ms' in error_template.lower():
            error_message = error_template.format(random.choice([5000, 10000, 30000, 60000]))
        elif 'index' in error_template.lower() and 'out of bounds' in error_template.lower():
            idx = random.randint(5, 10)
            size = random.randint(1, idx - 1)
            error_message = error_template.format(idx, size)
        elif 'cast' in error_template.lower() and placeholder_count >= 2:
            types = [('String', 'Integer'), ('Long', 'Double'), ('Object', 'TradeEntity')]
            type_pair = random.choice(types)
            error_message = error_template.format(*type_pair)
        elif 'port' in error_template.lower():
            error_message = error_template.format(random.choice([6379, 5432, 9092, 27017]))
        elif 'table' in error_template.lower():
            error_message = error_template.format(random.choice(['trades', 'positions', 'settlements']))
        elif 'bytes' in error_template.lower():
            error_message = error_template.format(random.choice([1048576, 2097152, 4194304]))
        elif placeholder_count == 1:
            error_message = error_template.format(random.choice([
                'counterparty', 'trade.quantity', 'settlement.date', 'trade.amount'
            ]))
        else:
            # Default: fill with generic values
            values = ['value1', 'value2', 'value3']
            error_message = error_template.format(*values[:placeholder_count])

        # Generate stacktrace
        trace = generate_stacktrace(template, template['chain_index'], error_message)

        # Generate remarks for CLOSED exceptions (70% closed, 30% open)
        status = 'CLOSED' if random.random() < 0.7 else 'OPEN'
        remarks = ''
        if status == 'CLOSED':
            remarks_template = random.choice(template['remarks_templates'])
            remarks_placeholder_count = remarks_template.count('{}')

            if remarks_placeholder_count == 0:
                remarks = remarks_template
            else:
                # Generate appropriate values based on template content
                values = []
                for _ in range(remarks_placeholder_count):
                    if 'ms' in remarks_template.lower() or 'timeout' in remarks_template.lower():
                        values.append(random.choice([30000, 60000, 120000]))
                    elif 'GB' in remarks_template or 'heap' in remarks_template.lower():
                        values.append(random.choice([2, 4, 8, 16]))
                    elif '%' in remarks_template:
                        values.append(random.choice([30, 40, 50]))
                    elif 'pool' in remarks_template.lower() or 'size' in remarks_template.lower():
                        values.append(random.choice([10, 20, 50, 100]))
                    elif 'host' in remarks_template.lower():
                        values.append(random.choice(['localhost', 'redis.prod.internal', 'db.internal']))
                    else:
                        values.append(random.choice(['field', 'value', 'parameter']))

                remarks = remarks_template.format(*values)

        exception = {
            'id': i + 1,
            'created_date': created_date.isoformat(),
            'destination': random.choice(['trade-ingestion-topic', 'trade-validation-topic', 'trade-processing-topic']),
            'error_message': error_message,
            'event_id': event_id,
            'event_id_type': 'UUID',
            'event_type': random.choice(['NEW', 'MODIFY', 'CANCEL']),
            'event_version': random.randint(1, 3),
            'exception_category': template['category'],
            'exception_sub_category': template['sub_category'],
            'exception_type': template['exception_type'],
            'host': f"trade-service-{random.randint(1, 5)}.prod.internal",
            'is_active': status == 'OPEN',
            'messaging_platform_type': 'KAFKA',
            'raising_system': random.choice(['trade-ingestion-service', 'trade-consumer-service', 'trade-validation-service']),
            'source_system': random.choice(['ATLAS', 'BLOOMBERG', 'MUREX']),
            'status': status,
            'times_replayed': random.randint(1, 20) if status == 'OPEN' else random.randint(1, 10),
            'updated_date': (created_date + timedelta(hours=random.randint(1, 48))).isoformat(),
            'updated_by': random.choice(['ops-team', 'dev-team', 'system-auto']),
            'comment': random.choice(['', 'Investigating', 'Escalated to L2', 'Awaiting upstream fix']),
            'trace': trace,
            'payload': '{}',  # Empty JSON for now
            'exception_id': exception_id,
            'remarks': remarks
        }

        exceptions.append(exception)

    return exceptions

def write_to_csv(exceptions, filename='data/exceptions.csv'):
    """Write exceptions to CSV file."""
    if not exceptions:
        print("No exceptions to write")
        return

    # Ensure data directory exists
    import os
    os.makedirs('data', exist_ok=True)

    fieldnames = list(exceptions[0].keys())

    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(exceptions)

    print(f"✅ Generated {len(exceptions)} exceptions in {filename}")

def main():
    """Generate sample data."""
    print("Generating 100 technical exceptions...")
    exceptions = generate_exceptions(100)

    # Print statistics
    categories = {}
    statuses = {}
    for exc in exceptions:
        categories[exc['exception_category']] = categories.get(exc['exception_category'], 0) + 1
        statuses[exc['status']] = statuses.get(exc['status'], 0) + 1

    print("\nStatistics:")
    print(f"  Categories: {categories}")
    print(f"  Statuses: {statuses}")

    write_to_csv(exceptions)
    print("\n✅ Sample data generated successfully!")

if __name__ == "__main__":
    main()
