import io
import zipfile
import boto3
import httpx  # Usamos httpx para requisições assíncronas
import asyncio
import hashlib  # Usamos hashlib para uma chave consistente
from typing import List, Optional
from botocore.exceptions import ClientError
from .s3 import BUCKET_RAW, presign_get

s3 = boto3.client("s3")

async def create_zip_from_keys(keys: List[str]) -> Optional[str]:
    """
    Cria um arquivo ZIP a partir de uma lista de chaves S3 de forma assíncrona.
    
    Esta função baixa os arquivos em paralelo, os compacta em memória,
    faz o upload do ZIP para o S3 e retorna uma URL pré-assinada para download.
    """
    if not keys:
        return None

    # 1. Geração de chave consistente para o arquivo ZIP usando MD5
    # Ordenamos as chaves para garantir que a mesma lista sempre produza o mesmo hash
    keys_tuple = tuple(sorted(keys))
    zip_hash = hashlib.md5(str(keys_tuple).encode()).hexdigest()
    zip_key = f"zips/search-result-{zip_hash}.zip"

    # Criar o buffer para o ZIP em memória
    zip_buffer = io.BytesIO()

    async with httpx.AsyncClient() as client:
        # Função interna para baixar e adicionar um único arquivo ao ZIP
        async def download_and_add_to_zip(key: str, zip_file: zipfile.ZipFile):
            try:
                # Pega o link pré-assinado
                url = presign_get(BUCKET_RAW, key)
                
                # Baixa a imagem de forma assíncrona
                resp = await client.get(url, timeout=30.0)
                resp.raise_for_status()  # Lança um erro para status
                
                # 2. Nome da imagem mais limpo dentro do zip
                # Remove o timestamp e o UUID, mantendo o nome original do arquivo
                original_filename = key.split("-", 2)[-1]
                zip_file.writestr(original_filename, resp.content)
                print(f"Adicionado ao ZIP: {original_filename}")

            except httpx.HTTPStatusError as e:
                print(f"Erro HTTP ao baixar {key}: {e.response.status_code}")
            except Exception as e:
                print(f"Erro ao processar a chave {key}: {e}")

        # Cria as tarefas para baixar todas as imagens em paralelo
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            tasks = [download_and_add_to_zip(key, zf) for key in keys]
            await asyncio.gather(*tasks)

    # Verifica se o ZIP não está vazio
    if not zip_buffer.getbuffer().nbytes:
        print("Buffer do ZIP está vazio. Nenhuma imagem foi adicionada.")
        return None

    zip_buffer.seek(0)

    # 3. Upload do zip no S3 com tratamento de erro
    try:
        s3.put_object(
            Bucket=BUCKET_RAW,
            Key=zip_key,
            Body=zip_buffer.getvalue(),
            ContentType='application/zip'
        )
        print(f"Upload do ZIP concluído para a chave: {zip_key}")
    except ClientError as e:
        print(f"Erro ao fazer upload do ZIP para o S3: {e}")
        return None

    # Retornar link pré-assinado para o arquivo ZIP
    return presign_get(BUCKET_RAW, zip_key, expires=3600)