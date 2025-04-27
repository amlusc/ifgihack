import json
from pathlib import Path
from typing import List
from langchain.schema import Document
from loguru import logger

class ThuenenAtlasConnector:
    """
    Connector class for reading and converting Thünen Atlas JSON metadata into LangChain documents.
    """

    def __init__(self, file_path: str = "./data/atlas.json"):
        """
        Initializes the connector by loading the JSON file.
        
        Args:
            file_path (str): Path to the JSON file containing the metadata.
        
        Raises:
            FileNotFoundError: If the specified file does not exist.
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        with open(self.file_path, "r", encoding="utf-8") as f:
            self.data = json.load(f)

    async def _features_to_docs(self) -> List[Document]:
        """
        Converts JSON metadata entries into a list of LangChain Document objects.
        
        Returns:
            List[Document]: A list of documents ready for indexing.
        """
        resources = self.data.get("resources", [])
        docs = []

        for res in resources:
            # Extract relevant fields with fallback values
            title = res.get("title", "No Title")
            abstract = res.get("abstract", "No Description")
            detail_url = res.get("detail_url", "")
            thumbnail = res.get("thumbnail_url", "")
            date = res.get("date", "")
            keywords = [kw.get("name") for kw in res.get("keywords", [])]
            extent = res.get("extent", {}).get("coords", [])

            # Compose the textual content of the document
            page_content = f"""Titel: {title}
            
Beschreibung: {abstract}

Link: {detail_url}
"""

            # Prepare document metadata
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

            # Handle spatial extent if available (convert to format expected by Leaflet)
            # 
            # Note: During the last 2-3 hours of the Hackathon, I tried assigning a generic BBOX 
            # to all documents in case they were missing one. The idea was that maybe documents 
            # weren't displayed in the frontend simply because no BBOX was present.
            # 
            # However, even after assigning a default BBOX, the frontend still doesn't render them properly. 
            # So the issue seems to lie somewhere else (e.g., parsing, visualization or frontend assumptions).
            if "extent" in res and isinstance(res["extent"], dict):
                coords = res["extent"].get("coords")
                if coords and isinstance(coords, list) and len(coords) == 4:
                    # Leaflet expects coordinates in [[south, west], [north, east]] format
                    sw = [coords[1], coords[0]]  # [south, west]
                    ne = [coords[3], coords[2]]  # [north, east]
                    metadata["bboxes"] = json.dumps([sw, ne])

            # Create a Document object and add it to the list
            docs.append(Document(page_content=page_content, metadata=metadata))

        logger.info(f"ThuenenAtlasConnector: {len(docs)} documents created.")
        return docs
