from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from supabase import create_client


def required(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def derive_key(passphrase: str, salt: bytes) -> bytes:
    return PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=600_000,
    ).derive(passphrase.encode("utf-8"))


def list_storage_files(bucket, prefix: str = "") -> list[str]:
    result: list[str] = []
    offset = 0
    while True:
        rows = bucket.list(prefix, {"limit": 100, "offset": offset, "sortBy": {"column": "name", "order": "asc"}}) or []
        if not rows:
            break
        for item in rows:
            name = str(item.get("name") or "")
            if not name:
                continue
            path = f"{prefix}/{name}" if prefix else name
            if item.get("id"):
                result.append(path)
            else:
                result.extend(list_storage_files(bucket, path))
        if len(rows) < 100:
            break
        offset += len(rows)
    return result


def main() -> None:
    database_url = required("RAZYNC_BACKUP_DATABASE_URL")
    supabase_url = required("RAZYNC_BACKUP_SUPABASE_URL")
    secret_key = required("RAZYNC_BACKUP_SUPABASE_SECRET_KEY")
    passphrase = required("RAZYNC_BACKUP_PASSPHRASE")
    output = Path(os.environ.get("RAZYNC_BACKUP_OUTPUT", "/tmp/razync-backup.rzenc"))

    with tempfile.TemporaryDirectory(prefix="razync-backup-") as temp_dir:
        root = Path(temp_dir)
        db_path = root / "database.dump"
        storage_dir = root / "storage"
        storage_dir.mkdir()

        subprocess.run(
            ["pg_dump", "--format=custom", "--no-owner", "--no-privileges", database_url, "--file", str(db_path)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            text=True,
        )

        client = create_client(supabase_url, secret_key)
        bucket = client.storage.from_("documents")
        files = list_storage_files(bucket)
        for storage_path in files:
            target = storage_dir / storage_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(bucket.download(storage_path))

        manifest = {
            "format": "razync-production-backup-v1",
            "database": "database.dump",
            "storage_bucket": "documents",
            "storage_object_count": len(files),
        }
        (root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        archive = root / "backup.zip"
        with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            zf.write(db_path, "database.dump")
            zf.write(root / "manifest.json", "manifest.json")
            for file_path in storage_dir.rglob("*"):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(root).as_posix())

        salt = os.urandom(16)
        nonce = os.urandom(12)
        key = derive_key(passphrase, salt)
        ciphertext = AESGCM(key).encrypt(nonce, archive.read_bytes(), b"Razync-Pro-Backup-v1")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(b"RZB1" + salt + nonce + ciphertext)
        shutil.rmtree(storage_dir, ignore_errors=True)

    print(f"Encrypted backup created at {output}")


if __name__ == "__main__":
    main()
