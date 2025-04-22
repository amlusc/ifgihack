from langchain.schema import Document
from owslib.csw import CatalogueServiceWeb
from owslib import fes
import json

# Class to retrieve documents from a Catalogue Service for the Web
class CSWRetriever:
    def __init__(self):
        # Define the CSW endpoint URL
        self.csw_url = "https://geoportal.bafg.de/csw"
        # Initialize the CSW service with a timeout
        self.csw = CatalogueServiceWeb(self.csw_url, timeout=10)
        # Store fetched documents
        self.docs = []

    def fetch_documents(self, keywords=["umwelt", "umweltdaten"], max_records=30):
        # Create a list of filters that match any of the keywords in the 'AnyText' field
        filter_list = [fes.PropertyIsLike(propertyname='csw:AnyText', literal=f'*{kw}*') for kw in keywords]
        # Combine the filters using logical OR
        final_filter = fes.Or(filter_list)
        # Perform the search query using the filters
        self.csw.getrecords2(constraints=[final_filter], maxrecords=max_records, esn='full')

        results = []

        # Iterate through the results returned by the CSW
        for rec_id, rec in self.csw.records.items():
            title = rec.title
            abstract = rec.abstract or ""
            links = rec.references or []
            # Extract URLs from the references (if available)
            urls = [l['url'] for l in links if 'url' in l]

            # Create a metadata dictionary
            metadata = {
                "title": title,
                "description": abstract,
                "url": urls[0] if urls else None,  # Use the first URL if available
            }

            # Create a LangChain Document with content and metadata
            doc = Document(
                page_content=abstract or title,
                metadata=metadata
            )
            results.append(doc)

        # Store the fetched documents
        self.docs = results
        return results

    def get_relevant_documents(self, query):
        # If no documents are stored yet, fetch them using the query as a keyword
        if not self.docs:
            self.fetch_documents(keywords=[query])
        return self.docs
