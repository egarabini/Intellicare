"""
============================================================================
NISE TRAINING MODULE - PERFORMANCE TESTS
============================================================================
Projeto: NISE - Treinamento Assistido
Módulo: API Performance Tests
Versão: 1.0
Data: 20/03/2026
Responsável: DEV2
============================================================================

Target: P99 < 100ms for all API endpoints
"""

import pytest
import time
import asyncio
from httpx import AsyncClient
from typing import List
import uuid

# ============================================================================
# PERFORMANCE TARGETS
# ============================================================================

P99_TARGET_MS = 100  # P99 should be under 100ms
P95_TARGET_MS = 50   # P95 should be under 50ms
P50_TARGET_MS = 25   # P50 should be under 25ms

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_percentile(values: List[float], percentile: int) -> float:
    """Calculate percentile from a list of values."""
    sorted_values = sorted(values)
    index = int(len(sorted_values) * (percentile / 100))
    return sorted_values[min(index, len(sorted_values) - 1)]


async def measure_endpoint_performance(
    client: AsyncClient,
    method: str,
    url: str,
    json_data: dict = None,
    iterations: int = 100
) -> dict:
    """
    Measure endpoint performance over multiple iterations.
    
    Returns:
        dict: Performance metrics (P50, P95, P99, avg, min, max)
    """
    response_times = []
    
    for _ in range(iterations):
        start_time = time.perf_counter()
        
        if method == "GET":
            await client.get(url)
        elif method == "POST":
            await client.post(url, json=json_data)
        elif method == "PUT":
            await client.put(url, json=json_data)
        elif method == "DELETE":
            await client.delete(url)
        
        end_time = time.perf_counter()
        response_times.append((end_time - start_time) * 1000)  # Convert to ms
    
    return {
        "p50": calculate_percentile(response_times, 50),
        "p95": calculate_percentile(response_times, 95),
        "p99": calculate_percentile(response_times, 99),
        "avg": sum(response_times) / len(response_times),
        "min": min(response_times),
        "max": max(response_times)
    }

# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

@pytest.mark.asyncio
@pytest.mark.performance
async def test_patient_create_performance(client: AsyncClient):
    """Test Patient creation performance."""
    sample_patient = {
        "resourceType": "Patient",
        "id": str(uuid.uuid4()),
        "name": [{"family": "Test", "given": ["Performance"]}],
        "gender": "male",
        "birthDate": "1990-01-01"
    }
    
    metrics = await measure_endpoint_performance(
        client, "POST", "/api/v1/patients/", sample_patient, iterations=50
    )
    
    print(f"\nPatient CREATE Performance:")
    print(f"  P50: {metrics['p50']:.2f}ms")
    print(f"  P95: {metrics['p95']:.2f}ms")
    print(f"  P99: {metrics['p99']:.2f}ms")
    
    assert metrics['p99'] < P99_TARGET_MS, f"P99 ({metrics['p99']:.2f}ms) exceeds target ({P99_TARGET_MS}ms)"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_patient_read_performance(client: AsyncClient):
    """Test Patient read performance."""
    # Create a patient first
    sample_patient = {
        "resourceType": "Patient",
        "id": "perf-test-patient",
        "name": [{"family": "Test", "given": ["Performance"]}],
        "gender": "male",
        "birthDate": "1990-01-01"
    }
    await client.post("/api/v1/patients/", json=sample_patient)
    
    metrics = await measure_endpoint_performance(
        client, "GET", "/api/v1/patients/perf-test-patient", iterations=100
    )
    
    print(f"\nPatient READ Performance:")
    print(f"  P50: {metrics['p50']:.2f}ms")
    print(f"  P95: {metrics['p95']:.2f}ms")
    print(f"  P99: {metrics['p99']:.2f}ms")
    
    assert metrics['p99'] < P99_TARGET_MS, f"P99 ({metrics['p99']:.2f}ms) exceeds target ({P99_TARGET_MS}ms)"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_patient_search_performance(client: AsyncClient):
    """Test Patient search performance."""
    # Create multiple patients
    for i in range(20):
        patient = {
            "resourceType": "Patient",
            "id": f"perf-patient-{i}",
            "name": [{"family": "TestFamily", "given": [f"Patient{i}"]}],
            "gender": "male",
            "birthDate": "1990-01-01"
        }
        await client.post("/api/v1/patients/", json=patient)
    
    metrics = await measure_endpoint_performance(
        client, "GET", "/api/v1/patients/?name=TestFamily", iterations=100
    )
    
    print(f"\nPatient SEARCH Performance:")
    print(f"  P50: {metrics['p50']:.2f}ms")
    print(f"  P95: {metrics['p95']:.2f}ms")
    print(f"  P99: {metrics['p99']:.2f}ms")
    
    assert metrics['p99'] < P99_TARGET_MS, f"P99 ({metrics['p99']:.2f}ms) exceeds target ({P99_TARGET_MS}ms)"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_observation_create_performance(client: AsyncClient):
    """Test Observation creation performance."""
    sample_observation = {
        "resourceType": "Observation",
        "id": str(uuid.uuid4()),
        "status": "final",
        "code": {"coding": [{"system": "http://loinc.org", "code": "2339-0"}]},
        "subject": {"reference": "Patient/test-123"}
    }
    
    metrics = await measure_endpoint_performance(
        client, "POST", "/api/v1/observations/", sample_observation, iterations=50
    )
    
    print(f"\nObservation CREATE Performance:")
    print(f"  P99: {metrics['p99']:.2f}ms")
    
    assert metrics['p99'] < P99_TARGET_MS


@pytest.mark.asyncio
@pytest.mark.performance
async def test_concurrent_requests(client: AsyncClient):
    """Test performance under concurrent load."""
    sample_patient = {
        "resourceType": "Patient",
        "id": str(uuid.uuid4()),
        "name": [{"family": "Concurrent", "given": ["Test"]}],
        "gender": "male"
    }
    
    # Create 10 concurrent requests
    tasks = [
        client.post("/api/v1/patients/", json={**sample_patient, "id": str(uuid.uuid4())})
        for _ in range(10)
    ]
    
    start_time = time.perf_counter()
    responses = await asyncio.gather(*tasks)
    end_time = time.perf_counter()
    
    total_time = (end_time - start_time) * 1000
    avg_time = total_time / len(tasks)
    
    print(f"\nConcurrent Requests Performance:")
    print(f"  Total time: {total_time:.2f}ms")
    print(f"  Average per request: {avg_time:.2f}ms")
    
    # All requests should succeed
    assert all(r.status_code == 201 for r in responses)
    
    # Average time should be reasonable
    assert avg_time < P99_TARGET_MS * 2  # Allow 2x target for concurrent load

