from fastapi import Request
from fastapi.responses import JSONResponse
import logging
from botocore.exceptions import BotoCoreError, ClientError
from typing import Union

log = logging.getLogger("errors")

async def botocore_error_handler(request: Request, exc: Union[BotoCoreError, ClientError]):
    log.exception("AWS error")
    return JSONResponse(status_code=500, content={"detail": "Erro de integração AWS."})

async def generic_error_handler(request: Request, exc: Exception):
    log.exception("Unhandled error")
    return JSONResponse(status_code=500, content={"detail": "Erro interno."})
