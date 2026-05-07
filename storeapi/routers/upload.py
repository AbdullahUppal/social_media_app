import logging
import tempfile

import aiofiles

# UploadFile in chuncks of 1MB and make it a complete file then we upload the file in b2 server and delete the tempfile
from fastapi import APIRouter, HTTPException, UploadFile, status

from lib.b2 import b2_upload_file

logger = logging.getLogger(__name__)

router = APIRouter()

CHUNK_SIZE = 1024 * 1024


@router.post("/upload", status_code=201)
async def upload_file(file: UploadFile):
    try:
        with tempfile.NamedTemporaryFile() as temp_file:
            filename = temp_file.name
            logger.info("savnig uploaded file temporarily")
            async with aiofiles.open(filename, "wb") as f:
                chunk = await file.read(CHUNK_SIZE)
                while chunk := await file.read(CHUNK_SIZE):
                    await f.write(chunk)

            file_url = b2_upload_file(local_file=filename, file_name=file.filename)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="There was an error upploading the file",
        )

    return {"details": f"Successfully uploaded {file.filename}", "file_url": file_url}
