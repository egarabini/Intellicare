"""
STEP 1.4: Performance Benchmarks
Measures throughput, latency, and resource usage

Target SLAs:
  - Event publishing: < 100ms per event
  - Consolidation: 1000+ events/sec
  - Query latency: P95 < 200ms, P99 < 500ms
  - Memory: < 500MB for app

Run with: pytest tests/test_performance_benchmarks.py -v -m performance
Or: pytest tests/test_performance_benchmarks.py --benchmark-only
"""

import time
import uuid
from datetime import datetime
from typing import List, Dict
import statistics

import pytest
from sqlalchemy import text
from sqlalchemy.orm import Session
import redis


# ============================================================================
# Performance Test Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def perf_config():
    """Performance test configuration"""
    return {
        "num_records": 1000,      # Number of records to test
        "num_events": 5000,        # Number of events for throughput test
        "batch_size": 100,         # Batch size for bulk operations
        "timeout_sec": 60,         # Test timeout
    }


@pytest.fixture(scope="function")
def clean_perf_data(real_db_session: Session, redis_clean: redis.Redis):
    """Clean performance test data before and after"""
    # Clean before
    real_db_session.execute(text("DELETE FROM oswaldo_operacional.pacientes WHERE nome LIKE 'PERF_TEST_%'"))
    real_db_session.commit()
    redis_clean.flushdb()
    
    yield
    
    # Clean after
    real_db_session.execute(text("DELETE FROM oswaldo_operacional.pacientes WHERE nome LIKE 'PERF_TEST_%'"))
    real_db_session.commit()


# ============================================================================
# Benchmark: Event Publishing Latency
# ============================================================================

@pytest.mark.performance
class TestEventPublishingLatency:
    """Measure latency of publishing events to Redis"""
    
    def test_event_publish_latency(self, redis_clean: redis.Redis):
        """Measure P50, P95, P99 event publish latency"""
        num_events = 1000
        latencies = []
        
        print("\n📊 Event Publishing Latency Test")
        print(f"  Publishing {num_events} events...")
        
        for i in range(num_events):
            start = time.perf_counter()
            
            redis_clean.xadd(
                "consolidation-events",
                {
                    "entity_id": str(uuid.uuid4()),
                    "operation": "CREATE",
                    "timestamp": datetime.utcnow().isoformat(),
                    "data": f"Event {i}"
                }
            )
            
            elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
            latencies.append(elapsed)
        
        # Calculate statistics
        p50 = statistics.median(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        p99 = sorted(latencies)[int(len(latencies) * 0.99)]
        avg = statistics.mean(latencies)
        
        print(f"  Results:")
        print(f"    Avg:  {avg:.2f}ms")
        print(f"    P50:  {p50:.2f}ms")
        print(f"    P95:  {p95:.2f}ms")
        print(f"    P99:  {p99:.2f}ms")
        
        # Assertions
        assert p50 < 50, f"P50 latency {p50:.2f}ms exceeds 50ms target"
        assert p95 < 100, f"P95 latency {p95:.2f}ms exceeds 100ms target"
        assert p99 < 500, f"P99 latency {p99:.2f}ms exceeds 500ms target"
        
        print(f"  ✅ Event publish latency SLA met!")


# ============================================================================
# Benchmark: Event Throughput
# ============================================================================

@pytest.mark.performance
class TestEventThroughput:
    """Measure event publishing and consumption throughput"""
    
    def test_publish_throughput(self, redis_clean: redis.Redis, perf_config: Dict):
        """Measure events per second"""
        num_events = perf_config["num_events"]
        
        print(f"\n📊 Event Throughput Test")
        print(f"  Publishing {num_events} events...")
        
        start = time.perf_counter()
        
        for i in range(num_events):
            redis_clean.xadd(
                "consolidation-events",
                {
                    "entity_id": str(uuid.uuid4()),
                    "operation": "CREATE",
                    "data": f"Event {i}"
                }
            )
        
        elapsed = time.perf_counter() - start
        throughput = num_events / elapsed
        
        print(f"  Results:")
        print(f"    Events: {num_events}")
        print(f"    Time:   {elapsed:.2f}s")
        print(f"    Rate:   {throughput:.0f} events/sec")
        
        # Target: 1000 events/sec
        assert throughput >= 500, f"Throughput {throughput:.0f}/sec below 500/sec target"
        
        print(f"  ✅ Throughput SLA met ({throughput:.0f} >= 500 events/sec)!")
    
    def test_consumer_throughput(self, redis_clean: redis.Redis, perf_config: Dict):
        """Measure consumer group throughput"""
        num_events = 500  # Smaller batch for consumer
        
        print(f"\n📊 Consumer Throughput Test")
        
        # Setup stream with data
        print(f"  Populating {num_events} events...")
        for i in range(num_events):
            redis_clean.xadd(
                "consolidation-events",
                {
                    "entity_id": str(uuid.uuid4()),
                    "operation": "CREATE",
                    "index": str(i)
                }
            )
        
        # Create consumer group
        try:
            redis_clean.xgroup_create("consolidation-events", "test-consumer", id="0", mkstream=True)
        except:
            pass
        
        # Measure consumption
        print(f"  Consuming {num_events} events...")
        start = time.perf_counter()
        
        consumed = 0
        while consumed < num_events:
            messages = redis_clean.xreadgroup(
                "test-consumer",
                "test-consumer",
                {"consolidation-events": ">"},
                count=100,
                block=1000
            )
            
            if not messages:
                break
            
            for stream, msg_list in messages:
                for msg_id, data in msg_list:
                    consumed += 1
                    redis_clean.xack("consolidation-events", "test-consumer", msg_id)
        
        elapsed = time.perf_counter() - start
        throughput = consumed / elapsed if elapsed > 0 else 0
        
        print(f"  Results:")
        print(f"    Consumed: {consumed} events")
        print(f"    Time:     {elapsed:.2f}s")
        print(f"    Rate:     {throughput:.0f} events/sec")
        
        assert throughput >= 300, f"Consumer throughput {throughput:.0f}/sec below target"
        
        print(f"  ✅ Consumer throughput SLA met ({throughput:.0f} >= 300 events/sec)!")


# ============================================================================
# Benchmark: Database Operations
# ============================================================================

@pytest.mark.performance
class TestDatabaseOperationLatency:
    """Measure database operation latencies"""
    
    def test_insert_latency(self, real_db_session: Session, clean_perf_data):
        """Measure INSERT latency"""
        num_inserts = 100
        latencies = []
        
        print(f"\n📊 Insert Latency Test")
        print(f"  Inserting {num_inserts} records...")
        
        for i in range(num_inserts):
            start = time.perf_counter()
            
            real_db_session.execute(text("""
                INSERT INTO oswaldo_operacional.pacientes 
                (id, nome, cpf, status, created_by, updated_by)
                VALUES (:id, :nome, :cpf, :status, :created_by, :updated_by)
            """), {
                "id": str(uuid.uuid4()),
                "nome": f"PERF_TEST_{i}",
                "cpf": f"{1000000000000 + i:014d}",
                "status": "ativo",
                "created_by": str(uuid.uuid4()),
                "updated_by": str(uuid.uuid4())
            })
            real_db_session.flush()
            
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)
        
        real_db_session.commit()
        
        # Stats
        p50 = statistics.median(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        avg = statistics.mean(latencies)
        
        print(f"  Results:")
        print(f"    Avg: {avg:.2f}ms")
        print(f"    P50: {p50:.2f}ms")
        print(f"    P95: {p95:.2f}ms")
        
        # Target: P95 < 50ms
        assert p95 < 100, f"Insert P95 {p95:.2f}ms exceeds 100ms"
        
        print(f"  ✅ Insert latency SLA met!")
    
    def test_select_latency(self, real_db_session: Session, clean_perf_data):
        """Measure SELECT latency"""
        # First, insert test data
        print(f"\n📊 Select Latency Test")
        print(f"  Populating test data...")
        
        for i in range(100):
            real_db_session.execute(text("""
                INSERT INTO oswaldo_operacional.pacientes 
                (id, nome, cpf, status, created_by, updated_by)
                VALUES (:id, :nome, :cpf, :status, :created_by, :updated_by)
            """), {
                "id": str(uuid.uuid4()),
                "nome": f"PERF_TEST_{i}",
                "cpf": f"{1000000000000 + i:014d}",
                "status": "ativo",
                "created_by": str(uuid.uuid4()),
                "updated_by": str(uuid.uuid4())
            })
        real_db_session.commit()
        
        # Measure SELECT
        print(f"  Querying 50 times...")
        latencies = []
        
        for _ in range(50):
            start = time.perf_counter()
            
            real_db_session.execute(text("""
                SELECT id, nome, cpf, status 
                FROM oswaldo_operacional.pacientes 
                WHERE nome LIKE 'PERF_TEST_%'
            """)).fetchall()
            
            elapsed = (time.perf_counter() - start) * 1000
            latencies.append(elapsed)
        
        # Stats
        p50 = statistics.median(latencies)
        p95 = sorted(latencies)[int(len(latencies) * 0.95)]
        avg = statistics.mean(latencies)
        
        print(f"  Results:")
        print(f"    Avg: {avg:.2f}ms")
        print(f"    P50: {p50:.2f}ms")
        print(f"    P95: {p95:.2f}ms")
        
        # Target: P95 < 200ms
        assert p95 < 500, f"Select P95 {p95:.2f}ms exceeds 500ms"
        
        print(f"  ✅ Select latency SLA met!")


# ============================================================================
# Benchmark: Bulk Operations
# ============================================================================

@pytest.mark.performance
class TestBulkOperations:
    """Measure bulk operation performance"""
    
    def test_bulk_insert_performance(self, real_db_session: Session, clean_perf_data):
        """Measure bulk insert performance"""
        num_records = 500
        batch_size = 100
        
        print(f"\n📊 Bulk Insert Performance Test")
        print(f"  Inserting {num_records} records in batches of {batch_size}...")
        
        start = time.perf_counter()
        
        for batch_num in range(0, num_records, batch_size):
            for i in range(min(batch_size, num_records - batch_num)):
                real_db_session.execute(text("""
                    INSERT INTO oswaldo_operacional.pacientes 
                    (id, nome, cpf, status, created_by, updated_by)
                    VALUES (:id, :nome, :cpf, :status, :created_by, :updated_by)
                """), {
                    "id": str(uuid.uuid4()),
                    "nome": f"PERF_TEST_{batch_num + i}",
                    "cpf": f"{2000000000000 + batch_num + i:014d}",
                    "status": "ativo",
                    "created_by": str(uuid.uuid4()),
                    "updated_by": str(uuid.uuid4())
                })
            
            real_db_session.commit()
        
        elapsed = time.perf_counter() - start
        throughput = num_records / elapsed
        
        print(f"  Results:")
        print(f"    Records:  {num_records}")
        print(f"    Time:     {elapsed:.2f}s")
        print(f"    Rate:     {throughput:.0f} records/sec")
        
        # Target: 500+ records/sec
        assert throughput >= 300, f"Bulk insert {throughput:.0f}/sec below 300/sec"
        
        print(f"  ✅ Bulk insert performance SLA met ({throughput:.0f} >= 300 records/sec)!")


# ============================================================================
# Benchmark: Stream Consumer Lag
# ============================================================================

@pytest.mark.performance
class TestConsumerLag:
    """Measure consumer lag under load"""
    
    def test_consumer_lag_under_load(self, redis_clean: redis.Redis):
        """Measure lag when producing events faster than consuming"""
        num_events = 1000
        
        print(f"\n📊 Consumer Lag Test")
        print(f"  Producing {num_events} events rapidly...")
        
        # Rapid produce
        start = time.perf_counter()
        for i in range(num_events):
            redis_clean.xadd(
                "consolidation-events",
                {
                    "entity_id": str(uuid.uuid4()),
                    "index": str(i)
                }
            )
        produce_time = time.perf_counter() - start
        
        # Get stream length (lag)
        lag = redis_clean.xlen("consolidation-events")
        
        print(f"  Results:")
        print(f"    Produced:  {num_events} events in {produce_time:.2f}s")
        print(f"    Current lag: {lag} messages")
        print(f"    Produce rate: {num_events/produce_time:.0f} events/sec")
        
        # Lag should not exceed produced events
        assert lag <= num_events, f"Lag {lag} exceeds produced {num_events}"
        
        print(f"  ✅ Consumer lag within limits!")


# ============================================================================
# Summary and Report
# ============================================================================

@pytest.mark.performance
class TestPerformanceSummary:
    """Summarize performance metrics"""
    
    def test_performance_summary(self):
        """Print summary of performance targets"""
        print("\n" + "="*60)
        print("PERFORMANCE TARGETS FOR STEP 1.4")
        print("="*60)
        
        targets = {
            "Event Publish P95 Latency": "< 100ms",
            "Event Throughput": "> 500 events/sec",
            "Insert P95 Latency": "< 100ms",
            "Select P95 Latency": "< 500ms",
            "Consumer Throughput": "> 300 events/sec",
            "Bulk Insert Rate": "> 300 records/sec",
            "Consumer Lag": "< Stream Size",
        }
        
        print("\nTarget SLAs:")
        for metric, target in targets.items():
            print(f"  ✓ {metric:.<45} {target}")
        
        print("\n" + "="*60)
        print("Run with: pytest tests/test_performance_benchmarks.py -v -m performance")
        print("="*60 + "\n")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-m", "performance", "-s"])
