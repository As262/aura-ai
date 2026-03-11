import concurrent.futures
import requests

URL = 'http://127.0.0.1:8000/api/usage-status/'


def fetch(i):
    resp = requests.get(URL, timeout=5)
    data = resp.json()
    return i, data.get('request_id'), data.get('server_timestamp')


if __name__ == '__main__':
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
        futures = [ex.submit(fetch, i) for i in range(10)]
        for f in concurrent.futures.as_completed(futures):
            i, rid, ts = f.result()
            print(f"{i}: {rid} @ {ts}")
