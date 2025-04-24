import json
from pathlib import Path
from typing import List
from langchain.schema import Document
from loguru import logger

class ThuenenAtlasConnector:
    def __init__(self, file_path: str = "./data/atlas.json"):
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"Datei nicht gefunden: {self.file_path}")
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    async def _features_to_docs(self) -> List[Document]:
        resources = self.data.get("resources", [])
        docs = []

        for res in resources:
            title = res.get("title", "Kein Titel")
            abstract = res.get("abstract", "Keine Beschreibung")
            detail_url = res.get("detail_url", "")
            thumbnail = res.get("thumbnail_url", "")
            date = res.get("date", "")
            keywords = [kw.get("name") for kw in res.get("keywords", [])]
            extent = res.get("extent", {}).get("coords", [])

            page_content = f"""Titel: {title}
            
Beschreibung: {abstract}

Link: {detail_url}
"""

            metadata = {
                "id": str(res.get("id")),
                "source": "Thünen Atlas",
                "date": date,
                "keywords": ", ".join(keywords) if keywords else "",
                "extent": str(extent),
                "thumbnail": thumbnail,
                "detail_url": detail_url,
                "title": title
            }

            # ✅ Korrektur: res statt entry
            if "extent" in res and isinstance(res["extent"], dict):
                coords = res["extent"].get("coords")
                if coords and isinstance(coords, list) and len(coords) == 4:
                    # Leaflet expects [[south, west], [north, east]]
                    sw = [coords[1], coords[0]]  # [south, west]
                    ne = [coords[3], coords[2]]  # [north, east]
                    metadata["bboxes"] = json.dumps([sw, ne])


            docs.append(Document(page_content=page_content, metadata=metadata))

        logger.info(f"ThuenenAtlasConnector: {len(docs)} Dokumente erstellt.")
        return docs
