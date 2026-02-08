# backend/api/upload.py
import shutil
import uuid
import os
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, Request, HTTPException

router = APIRouter()

@router.post("/api/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    try:
        current_file = Path(__file__).resolve()
        backend_dir = current_file.parent.parent
        upload_dir = backend_dir / "static" / "uploads"
        
        upload_dir.mkdir(parents=True, exist_ok=True)
        
        filename = file.filename
        ext = os.path.splitext(filename)[1] if filename else ".jpg"
        new_filename = f"{uuid.uuid4().hex}{ext}"
        file_path = upload_dir / new_filename
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 【核心修正】返回根相对路径，不带 http://localhost
        # 这样部署到任何域名下，图片链接都自动适配
        file_url = f"/static/uploads/{new_filename}"
        
        return {"url": file_url}

    except Exception as e:
        print(f"上传失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
