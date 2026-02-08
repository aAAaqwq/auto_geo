import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from backend.services.site_generator import SiteGeneratorService
from backend.services.deploy_service import DeployService

router = APIRouter(prefix="/sites", tags=["Site Builder"])
generator = SiteGeneratorService()
deployer = DeployService()

# 1. 构建请求模型
class SiteBuildRequest(BaseModel):
    name: str
    config: dict
    template_id: str = "corporate" 
# 2. 部署请求模型
class DeployRequest(BaseModel):
    site_id: str
    project_name: str
    method: str
    
    sftp_host: Optional[str] = None
    sftp_port: Optional[int] = 22
    sftp_user: Optional[str] = None
    sftp_pass: Optional[str] = None
    sftp_path: Optional[str] = "/var/www/html"
    
    custom_domain: Optional[str] = None
    
    s3_endpoint: Optional[str] = None
    s3_bucket: Optional[str] = None
    s3_access_key: Optional[str] = None
    s3_secret_key: Optional[str] = None
    s3_region: Optional[str] = None

@router.post("/build")
def build_new_site(req: SiteBuildRequest):
    site_id = uuid.uuid4().hex
    result = generator.generate_site(site_id, req.config, req.template_id)
    result['site_id'] = site_id
    return {"code": 200, "data": result}

@router.post("/deploy")
def deploy_site(req: DeployRequest):
    try:
        if req.method == 'sftp':
            result = deployer.deploy_sftp(
                site_id=req.site_id,
                project_name=req.project_name,
                host=req.sftp_host,
                port=req.sftp_port,
                username=req.sftp_user,
                password=req.sftp_pass,
                remote_root=req.sftp_path,
                custom_domain=req.custom_domain
            )
        elif req.method == 's3':
            result = deployer.deploy_s3(
                site_id=req.site_id,
                endpoint=req.s3_endpoint,
                bucket=req.s3_bucket,
                access_key=req.s3_access_key,
                secret_key=req.s3_secret_key,
                region=req.s3_region
            )
        else:
            raise HTTPException(status_code=400, detail="Unknown method")
            
        return {"code": 200, "data": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
