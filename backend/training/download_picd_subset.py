"""Download a reproducible, broad-label subset of the public PICD dataset.

The complete PICD release contains fine-grained composition annotations. This
script uses only high-precision source categories that map to the application's
four matching labels:

* POINT_1_ROT -> rule_of_thirds
* POINT_SHAPE_CENT -> centered
* POINT_MULTI_DIA/DIA -> diagonal
* PERSPECTIVE/LINE_VERTI2/LINE_VERTI3/LINE_VERTI_MANY -> leading_lines

Files are downloaded outside the repository by default. They are auxiliary
pretraining data only; the application's fixed local validation/test split is
never modified.
"""
import argparse
import json
import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests
from PIL import Image
from io import BytesIO


DRIVE_ROOT = '1YbOTZavrKefwYYmhNQmp1umbWmKMG1Ox'
GROUPS = {
    'rule_of_thirds': ('POINT_1_ROT',),
    'centered': ('POINT_SHAPE_CENT',),
    'diagonal': ('POINT_MULTI_DIA', 'DIA'),
    'leading_lines': ('PERSPECTIVE', 'LINE_VERTI2', 'LINE_VERTI3', 'LINE_VERTI_MANY'),
}


def folder_children(session, folder_id):
    from bs4 import BeautifulSoup

    response = session.get(f'https://drive.google.com/embeddedfolderview?id={folder_id}', timeout=90)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, 'html.parser')
    children = []
    for anchor in soup.find_all('a'):
        href = anchor.get('href', '')
        text = anchor.get_text(strip=True)
        file_match = re.search(r'/file/d/([\w-]+)/view', href)
        if file_match:
            children.append((file_match.group(1), text))
        else:
            folder_match = re.search(r'/folders/([\w-]+)', href)
            if folder_match:
                children.append((folder_match.group(1), text))
    return children


def download_one(item, output, label):
    file_id, source_name, source_group = item
    target = output / label / f'{source_group}_{source_name}'
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and target.stat().st_size > 1024:
        return target, True
    url = f'https://drive.usercontent.google.com/download?id={file_id}&export=download'
    for attempt in range(3):
        try:
            response = requests.get(url, timeout=90)
            response.raise_for_status()
            image = Image.open(BytesIO(response.content)).convert('RGB')
            image.thumbnail((640, 640))
            image.save(target, format='JPEG', quality=92)
            return target, True
        except Exception:
            if attempt == 2:
                return target, False
    return target, False


def main(args):
    output = args.output
    output.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    root = {name: folder_id for folder_id, name in folder_children(session, DRIVE_ROOT)}
    source_folders = {}
    for names in GROUPS.values():
        for name in names:
            if name not in root:
                raise ValueError(f'PICD folder not found: {name}')
            source_folders[name] = root[name]

    rng = random.Random(args.seed)
    selected = []
    for label, groups in GROUPS.items():
        per_group = max(1, args.per_label // len(groups))
        for source_group in groups:
            children = [(file_id, name) for file_id, name in folder_children(session, source_folders[source_group])
                        if name.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))]
            children.sort(key=lambda row: row[1])
            if len(children) > per_group:
                children = rng.sample(children, per_group)
            selected.extend((file_id, name, source_group, label) for file_id, name in children)
            print(f'{source_group}: selected {len(children)} of {len(folder_children(session, source_folders[source_group]))}', flush=True)

    manifest = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(download_one, (file_id, name, source_group), output, label):
                   (file_id, name, source_group, label)
                   for file_id, name, source_group, label in selected}
        for index, future in enumerate(as_completed(futures), 1):
            file_id, name, source_group, label = futures[future]
            target, ok = future.result()
            if ok:
                manifest.append(dict(path=str(target), label=label, source_group=source_group,
                                     source_name=name, drive_id=file_id))
            if index % 100 == 0 or index == len(futures):
                print(f'Downloaded {index}/{len(futures)}; valid={len(manifest)}', flush=True)

    (output / 'manifest.json').write_text(json.dumps({
        'dataset': 'PICD', 'source_folder': DRIVE_ROOT, 'seed': args.seed,
        'per_label_target': args.per_label, 'workers': args.workers,
        'mapping': GROUPS, 'samples': sorted(manifest, key=lambda row: row['path']),
    }, indent=2), encoding='utf-8')
    print(f'Wrote {len(manifest)} valid samples to {output}', flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(r'C:\tmp\agent-tmp\picd_subset'))
    parser.add_argument('--per-label', type=int, default=600)
    parser.add_argument('--workers', type=int, default=12)
    parser.add_argument('--seed', type=int, default=42)
    main(parser.parse_args())
