#!/usr/bin/env python3
"""
Bonifade Technologies Swarm — Cloudflare R2 / S3 Storage Engine.
Provides high-performance, pure-Python AWS SigV4 signed operations
for Cloudflare R2 object storage without requiring the heavy AWS CLI.
"""

import datetime
import hashlib
import hmac
import os
import sys
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

# Terminal Colors
GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
CYAN = "\033[0;36m"
BOLD = "\033[1m"
NC = "\033[0m"


class CloudflareR2:
    def __init__(
        self,
        account_id: Optional[str] = None,
        access_key_id: Optional[str] = None,
        secret_access_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        endpoint_url: Optional[str] = None,
    ):
        self.account_id = account_id or os.getenv("R2_ACCOUNT_ID", "").strip()
        self.access_key_id = access_key_id or os.getenv("R2_ACCESS_KEY_ID", "").strip()
        self.secret_access_key = secret_access_key or os.getenv("R2_SECRET_ACCESS_KEY", "").strip()
        self.bucket_name = bucket_name or os.getenv("R2_BUCKET_NAME", "bonifade-buzz-storage").strip()

        if endpoint_url:
            self.endpoint = endpoint_url.rstrip("/")
        elif self.account_id:
            self.endpoint = f"https://{self.account_id}.r2.cloudflarestorage.com"
        else:
            self.endpoint = os.getenv("R2_ENDPOINT", "").rstrip("/")

        self.region = "auto"
        self.service = "s3"

    def is_configured(self) -> bool:
        return bool(self.access_key_id and self.secret_access_key and self.endpoint and self.bucket_name)

    def _sign(self, key: bytes, msg: str) -> bytes:
        return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

    def _get_signature_key(self, key: str, date_stamp: str, region_name: str, service_name: str) -> bytes:
        k_date = self._sign(("AWS4" + key).encode("utf-8"), date_stamp)
        k_region = hmac.new(k_date, region_name.encode("utf-8"), hashlib.sha256).digest()
        k_service = hmac.new(k_region, service_name.encode("utf-8"), hashlib.sha256).digest()
        k_signing = hmac.new(k_service, "aws4_request".encode("utf-8"), hashlib.sha256).digest()
        return k_signing

    def _request(
        self,
        method: str,
        path: str,
        data: Optional[bytes] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> urllib.request.Request:
        if headers is None:
            headers = {}

        now = datetime.datetime.now(datetime.timezone.utc)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")

        url_path = f"/{self.bucket_name}/{path.lstrip('/')}"
        url = f"{self.endpoint}{url_path}"
        parsed_url = urllib.parse.urlparse(url)
        host = parsed_url.netloc

        payload_hash = hashlib.sha256(data if data else b"").hexdigest()

        headers["host"] = host
        headers["x-amz-date"] = amz_date
        headers["x-amz-content-sha256"] = payload_hash

        # Canonical Headers
        sorted_headers = sorted(headers.items(), key=lambda x: x[0].lower())
        canonical_headers = "".join([f"{k.lower()}:{v.strip()}\n" for k, v in sorted_headers])
        signed_headers = ";".join([k.lower() for k, _ in sorted_headers])

        canonical_uri = parsed_url.path
        canonical_querystring = parsed_url.query

        canonical_request = (
            f"{method}\n{canonical_uri}\n{canonical_querystring}\n"
            f"{canonical_headers}\n{signed_headers}\n{payload_hash}"
        )

        algorithm = "AWS4-HMAC-SHA256"
        credential_scope = f"{date_stamp}/{self.region}/{self.service}/aws4_request"
        string_to_sign = (
            f"{algorithm}\n{amz_date}\n{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()}"
        )

        signing_key = self._get_signature_key(self.secret_access_key, date_stamp, self.region, self.service)
        signature = hmac.new(signing_key, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        authorization_header = (
            f"{algorithm} Credential={self.access_key_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )

        req_headers = dict(headers)
        req_headers["Authorization"] = authorization_header

        return urllib.request.Request(url, data=data, headers=req_headers, method=method)

    def upload_file(self, local_path: str, remote_path: str) -> bool:
        if not self.is_configured():
            print(f"{RED}Error: Cloudflare R2 is not configured in .env{NC}")
            return False

        if not os.path.isfile(local_path):
            print(f"{RED}Error: File '{local_path}' not found.{NC}")
            return False

        with open(local_path, "rb") as f:
            data = f.read()

        file_size_mb = len(data) / (1024 * 1024)
        print(f"  Uploading {BOLD}{local_path}{NC} ({file_size_mb:.2f} MB) -> {CYAN}r2://{self.bucket_name}/{remote_path}{NC}...")

        try:
            req = self._request("PUT", remote_path, data=data)
            with urllib.request.urlopen(req, timeout=120) as resp:
                if resp.status in [200, 201]:
                    print(f"  {GREEN}✓ Uploaded to R2 successfully.{NC}")
                    return True
                else:
                    print(f"  {RED}✗ R2 upload failed with status {resp.status}{NC}")
                    return False
        except Exception as e:
            print(f"  {RED}✗ Upload error: {e}{NC}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        if not self.is_configured():
            print(f"{RED}Error: Cloudflare R2 is not configured in .env{NC}")
            return False

        os.makedirs(os.path.dirname(os.path.abspath(local_path)), exist_ok=True)
        print(f"  Downloading {CYAN}r2://{self.bucket_name}/{remote_path}{NC} -> {BOLD}{local_path}{NC}...")

        try:
            req = self._request("GET", remote_path)
            with urllib.request.urlopen(req, timeout=120) as resp:
                if resp.status == 200:
                    with open(local_path, "wb") as f:
                        f.write(resp.read())
                    print(f"  {GREEN}✓ Downloaded from R2 successfully ({os.path.getsize(local_path)/(1024*1024):.2f} MB).{NC}")
                    return True
                else:
                    print(f"  {RED}✗ Download failed with status {resp.status}{NC}")
                    return False
        except Exception as e:
            print(f"  {RED}✗ Download error: {e}{NC}")
            return False

    def list_objects(self, prefix: str = "") -> List[Dict[str, Any]]:
        """Lists objects in the bucket matching prefix."""
        if not self.is_configured():
            return []
        try:
            # Query S3 list-objects-v2 via GET
            req = self._request("GET", f"?list-type=2&prefix={urllib.parse.quote(prefix)}")
            with urllib.request.urlopen(req, timeout=30) as resp:
                xml_data = resp.read().decode("utf-8")
                # Simple XML tag extraction without external lxml dependency
                import xml.etree.ElementTree as ET
                root = ET.fromstring(xml_data)
                ns = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}
                items = []
                for content in root.findall("s3:Contents", ns):
                    key = content.find("s3:Key", ns).text
                    size = int(content.find("s3:Size", ns).text)
                    last_mod = content.find("s3:LastModified", ns).text
                    items.append({"key": key, "size": size, "last_modified": last_mod})
                return items
        except Exception as e:
            print(f"  {YELLOW}R2 List Warning: {e}{NC}")
            return []


def main():
    r2 = CloudflareR2()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "status"

    if cmd == "status":
        print(f"\n{CYAN}{BOLD}══ Cloudflare R2 Storage Status ═════════════════════════════════════════{NC}")
        if r2.is_configured():
            print(f"  Status:       {GREEN}Configured & Active{NC}")
            print(f"  Account ID:   {r2.account_id}")
            print(f"  Bucket:       {r2.bucket_name}")
            print(f"  Endpoint:     {r2.endpoint}")
            objects = r2.list_objects()
            print(f"  Total Stored: {len(objects)} objects")
            for obj in objects[:10]:
                print(f"    • {obj['key']} ({obj['size']/(1024*1024):.2f} MB, {obj['last_modified']})")
        else:
            print(f"  Status:       {YELLOW}Not Configured in .env{NC}")
            print("  Set R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY in .env")
        print(f"{CYAN}{BOLD}═════════════════════════════════════════════════════════════════════════{NC}\n")

    elif cmd == "upload" and len(sys.argv) > 3:
        r2.upload_file(sys.argv[2], sys.argv[3])
    elif cmd == "download" and len(sys.argv) > 3:
        r2.download_file(sys.argv[2], sys.argv[3])
    elif cmd == "sync-marketing":
        print(f"\n{CYAN}{BOLD}Syncing Marketing Knowledge Base to Cloudflare R2...{NC}")
        m_dir = "marketing/knowledge"
        if os.path.exists(m_dir):
            for fname in os.listdir(m_dir):
                fpath = os.path.join(m_dir, fname)
                if os.path.isfile(fpath):
                    r2.upload_file(fpath, f"marketing/knowledge/{fname}")
        print(f"{GREEN}✓ Marketing Knowledge Base synced to R2.{NC}\n")
    else:
        print("Usage: ./scripts/r2_storage.py [status|upload <local> <remote>|download <remote> <local>|sync-marketing]")


if __name__ == "__main__":
    main()
