import os
import requests
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Directorio de salida
OUTPUT_DIR = "data/clinical_guides/esmo"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Europe PMC API para buscar guías ESMO en Open Access con PDF
# Buscamos "ESMO clinical practice guidelines" y exigimos PDF y acceso abierto
EPMC_API_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"

def main():
    logger.info("Iniciando descarga automática de Guías ESMO (Open Access)...")
    
    params = {
        "query": '("ESMO Clinical Practice Guidelines" OR "ESMO Clinical Practice Guideline") AND (FORMAT:"pdf") AND (OPEN_ACCESS:"Y")',
        "format": "json",
        "resultType": "core",
        "pageSize": 20 # Traemos las primeras 20 para armar una base sólida pero rápida
    }
    
    try:
        response = requests.get(EPMC_API_URL, params=params)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        logger.error(f"Error al conectar con Europe PMC: {e}")
        return

    results = data.get("resultList", {}).get("result", [])
    if not results:
        logger.warning("No se encontraron resultados en Europe PMC con los parámetros dados.")
        return
        
    logger.info(f"Se encontraron {len(results)} artículos. Buscando enlaces PDF...")
    
    downloaded = 0
    for article in results:
        pmcid = article.get("pmcid")
        title = article.get("title", "Sin_Titulo")
        
        # Limpiar el título para nombre de archivo
        safe_title = "".join(c if c.isalnum() else "_" for c in title)
        safe_title = safe_title[:50] # Acortar si es muy largo
        
        fullTextUrlList = article.get("fullTextUrlList", {}).get("fullTextUrl", [])
        pdf_url = None
        for url_info in fullTextUrlList:
            if url_info.get("documentStyle") == "pdf":
                pdf_url = url_info.get("url")
                break
                
        if pdf_url and pmcid:
            filename = f"ESMO_{pmcid}_{safe_title}.pdf"
            filepath = os.path.join(OUTPUT_DIR, filename)
            
            if os.path.exists(filepath):
                logger.info(f"El archivo {filename} ya existe, saltando.")
                continue
                
            logger.info(f"Descargando: {title}...")
            try:
                # Descargamos con un header User-Agent para evitar rechazos
                headers = {"User-Agent": "Mozilla/5.0 (compatible; OncoAgent/1.0; +https://github.com/maximolopezchenlo-lab/OncoAgent)"}
                pdf_response = requests.get(pdf_url, headers=headers, stream=True)
                pdf_response.raise_for_status()
                
                with open(filepath, "wb") as f:
                    for chunk in pdf_response.iter_content(chunk_size=8192):
                        f.write(chunk)
                downloaded += 1
            except Exception as e:
                logger.error(f"Error descargando {pdf_url}: {e}")
                
    logger.info(f"Descarga finalizada. {downloaded} PDFs de guías ESMO guardados en {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
