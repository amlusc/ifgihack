# server/connectors/csw_connector.py

from langchain.schema import Document
from owslib.csw import CatalogueServiceWeb
from owslib import fes
import json


class CSWRetriever:
    def __init__(self):
        self.csw_url = "https://geoportal.bafg.de/csw"
        self.csw = CatalogueServiceWeb(self.csw_url, timeout=10)
        self.docs = []

    def fetch_documents(self, keywords=["umwelt", "umweltdaten"], max_records=30):
        filter_list = [fes.PropertyIsLike(propertyname='csw:AnyText', literal=f'*{kw}*') for kw in keywords]
        final_filter = fes.Or(filter_list)
        self.csw.getrecords2(constraints=[final_filter], maxrecords=max_records, esn='full')

        results = []
        for rec_id, rec in self.csw.records.items():
            title = rec.title
            abstract = rec.abstract or ""
            links = rec.references or []
            urls = [l['url'] for l in links if 'url' in l]

            metadata = {
                "title": title,
                "description": abstract,
                "url": urls[0] if urls else None,
            }

            doc = Document(
                page_content=abstract or title,
                metadata=metadata
            )
            results.append(doc)

        self.docs = results
        return results

    def get_relevant_documents(self, query):
        if not self.docs:
            self.fetch_documents(keywords=[query])
        return self.docs
