import pytest
from dask.distributed import LocalCluster, Client

print("Loading conftest.py")

import time

@pytest.fixture(scope='session')
def dask_client():
    print(f"\n[Dask Client] Starting Dask LocalCluster at {time.time()}")
    cluster = LocalCluster(n_workers=1, threads_per_worker=1, processes=False, asynchronous=False) # Use single worker for predictable testing
    client = Client(cluster)
    print(f"[Dask Client] Dask LocalCluster started at {time.time()}")
    yield client
    client.close()
    cluster.close()
    print(f"[Dask Client] Dask LocalCluster closed at {time.time()}")