"""Download the human-rated AVA subset, verifying each pinned source shard.

python training/download_public_data.py --output training_data/public/ava
Images are resized to 320px for local training; original human vote counts are preserved.
Owned download shards are removed after conversion to keep disk usage bounded.
"""
import argparse
import hashlib
import io
import json
import time
from pathlib import Path

from PIL import Image, ImageOps
import pyarrow.parquet as pq
import requests

REPOSITORY = 'trojblue/AVA-aesthetics-10pct-min50-10bins'
REVISION = 'ee09ff2b4151b87c61cfb5165bb46c0ebe39b679'


def download_ava(output):
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    images = output / 'images'
    images.mkdir(exist_ok=True)
    url = f'https://huggingface.co/api/datasets/{REPOSITORY}/tree/{REVISION}?recursive=true&limit=100'
    response = requests.get(url, timeout=60)
    response.raise_for_status()
    files = [row for row in response.json() if row['path'].endswith('.parquet')
             and not row['path'].startswith('data/test-')]
    rows, sources, seen, invalid = [], [], set(), []
    for entry in sorted(files, key=lambda row: row['path']):
        path = output / Path(entry['path']).name
        source_url = f"https://huggingface.co/datasets/{REPOSITORY}/resolve/{REVISION}/{entry['path']}"
        expected = entry['lfs']['oid']
        if not path.exists():
            for attempt in range(4):
                try:
                    print(f"Downloading {entry['path']} ({entry['size'] / 1e6:.0f} MB)", flush=True)
                    with requests.get(source_url, stream=True, timeout=(30, 120)) as stream:
                        stream.raise_for_status()
                        with path.with_suffix('.partial').open('wb') as handle:
                            for block in stream.iter_content(1024 * 1024):
                                handle.write(block)
                    path.with_suffix('.partial').replace(path)
                    break
                except requests.RequestException:
                    if attempt == 3:
                        raise
                    time.sleep(2 ** attempt)
        digest = hashlib.sha256()
        with path.open('rb') as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b''):
                digest.update(block)
        if digest.hexdigest() != expected:
            raise ValueError(f'Checksum failed for {path}; remove the incomplete shard and retry')
        split = 'train' if '/train-' in entry['path'] else 'holdout'
        for batch in pq.ParquetFile(path).iter_batches(batch_size=64):
            for row in batch.to_pylist():
                counts = row['rating_counts']
                if len(counts) != 10 or sum(counts) < 50:
                    raise ValueError('Unexpected AVA label schema')
                image_bytes = row['image']['bytes']
                image_hash = hashlib.sha256(image_bytes).hexdigest()
                if image_hash in seen:
                    continue
                try:
                    with Image.open(io.BytesIO(image_bytes)) as image:
                        image = ImageOps.exif_transpose(image).convert('RGB')
                        image.thumbnail((320, 320))
                        image_path = images / f"{row['image_id']}.jpg"
                        image.save(image_path, quality=94)
                except Exception as exc:
                    invalid.append(dict(image_id=row['image_id'], error=str(exc)))
                    continue
                seen.add(image_hash)
                # Reserve half of the publisher's holdout by stable ID; never train on either half.
                final_split = split if split == 'train' else (
                    'validation' if int(hashlib.sha256(str(row['image_id']).encode()).hexdigest()[:8], 16) % 2 else 'test')
                rows.append(dict(image_id=row['image_id'], image=f"images/{row['image_id']}.jpg",
                                 sha256=image_hash, rating_counts=counts, split=final_split))
        sources.append(dict(path=entry['path'], sha256=expected, bytes=entry['size']))
        manifest = dict(dataset=REPOSITORY, revision=REVISION, source_shards=sources,
                        preprocessing='EXIF transpose, RGB, thumbnail <=320px, JPEG quality 94',
                        samples=rows, invalid=invalid, complete=len(sources) == len(files))
        (output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        path.unlink()  # this script's verified temporary source shard, not an existing user dataset
        print(f"Prepared {len(rows):,} labeled images so far", flush=True)
    return manifest


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).resolve().parents[1] / 'training_data/public/ava')
    download_ava(parser.parse_args().output)
