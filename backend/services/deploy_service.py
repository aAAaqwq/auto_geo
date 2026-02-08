import os
import mimetypes
from pathlib import Path
import logging
import paramiko
import boto3
import re

logger = logging.getLogger("deploy")

class DeployService:
    def __init__(self):
        self.base_dir = Path(__file__).resolve().parent.parent
        self.sites_dir = self.base_dir / "static" / "sites"

    def _get_site_path(self, site_id: str):
        path = self.sites_dir / site_id
        if not path.exists():
            raise FileNotFoundError(f"Site ID {site_id} not found.")
        return path

    def _sanitize_name(self, name: str):
        safe_name = re.sub(r'[^a-zA-Z0-9]', '_', name).lower()
        return re.sub(r'_+', '_', safe_name).strip('_')

    def deploy_sftp(self, site_id: str, project_name: str, host: str, port: int, username: str, password: str, remote_root: str, custom_domain: str = None):
        local_path = self._get_site_path(site_id)
        folder_name = self._sanitize_name(project_name)
        target_remote_dir = f"{remote_root.rstrip('/')}/{folder_name}"
        
        try:
            transport = paramiko.Transport((host, int(port)))
            transport.banner_timeout = 30
            transport.connect(username=username, password=password)
            sftp = paramiko.SFTPClient.from_transport(transport)

            def _upload_dir(local_dir, remote_dir):
                try: sftp.stat(remote_dir)
                except FileNotFoundError: sftp.mkdir(remote_dir)
                for item in os.listdir(local_dir):
                    l_path = os.path.join(local_dir, item)
                    r_path = f"{remote_dir}/{item}".replace("//", "/")
                    if os.path.isfile(l_path): sftp.put(l_path, r_path)
                    elif os.path.isdir(l_path): _upload_dir(l_path, r_path)

            _upload_dir(str(local_path), target_remote_dir)
            sftp.close()
            transport.close()

            if custom_domain:
                public_url = f"{custom_domain.rstrip('/')}/{folder_name}/index.html"
            else:
                public_url = f"http://{host}/{folder_name}/index.html"

            return {"status": "success", "message": "Deployed", "url": public_url}

        except Exception as e:
            logger.error(f"SFTP Error: {e}")
            raise Exception(f"Deployment Failed: {str(e)}")

    def deploy_s3(self, site_id: str, endpoint: str, bucket: str, access_key: str, secret_key: str, region: str = None):
        local_path = self._get_site_path(site_id)
        try:
            s3_config = {
                'aws_access_key_id': access_key,
                'aws_secret_access_key': secret_key,
            }
            if endpoint: s3_config['endpoint_url'] = endpoint
            if region: s3_config['region_name'] = region

            s3 = boto3.client('s3', **s3_config)

            for root, dirs, files in os.walk(local_path):
                for file in files:
                    full_path = os.path.join(root, file)
                    relative_path = os.path.relpath(full_path, local_path).replace("\\", "/")
                    content_type = mimetypes.guess_type(full_path)[0] or 'application/octet-stream'
                    
                    s3.upload_file(
                        Filename=full_path,
                        Bucket=bucket,
                        Key=relative_path,
                        ExtraArgs={'ContentType': content_type, 'ACL': 'public-read'}
                    )

            if "aliyuncs" in endpoint:
                url = f"https://{bucket}.{endpoint.split('//')[1]}/{'index.html'}"
            else:
                url = f"{endpoint}/{bucket}/index.html"

            return {"status": "success", "message": "Cloud Upload Complete", "url": url}

        except Exception as e:
            logger.error(f"S3 Error: {e}")
            raise Exception(f"Cloud Storage Error: {str(e)}")
