import os
import shutil
from typing import List
from langchain_core.documents import Document
from deeprag.loader.file_loader.base import BaseLoader


class UnstructuredLoader(BaseLoader):
    def __init__(self):
        self.directory_with_results = "./pdf_processed_outputs"
        shutil.rmtree(self.directory_with_results)
        os.makedirs(self.directory_with_results)

    def load_file(self, file_path: str) -> List[Document]:
        ...  #TODO

    def load_directory(self, directory: str) -> List[Document]:
        from unstructured_ingest.v2.pipeline.pipeline import Pipeline
        from unstructured_ingest.v2.interfaces import ProcessorConfig
        from unstructured_ingest.v2.processes.connectors.local import (
            LocalIndexerConfig,
            LocalDownloaderConfig,
            LocalConnectionConfig,
            LocalUploaderConfig,
        )
        from unstructured_ingest.v2.processes.partitioner import PartitionerConfig

        Pipeline.from_configs(
            context=ProcessorConfig(),
            indexer_config=LocalIndexerConfig(input_path=directory),
            downloader_config=LocalDownloaderConfig(),
            source_connection_config=LocalConnectionConfig(),
            partitioner_config=PartitionerConfig(
                partition_by_api=True,
                api_key=os.getenv("UNSTRUCTURED_API_KEY"),
                partition_endpoint=os.getenv("UNSTRUCTURED_API_URL"),
                strategy="hi_res",
                additional_partition_args={
                    "split_pdf_page": True,
                    "split_pdf_concurrency_level": 15,
                },
            ),
            uploader_config=LocalUploaderConfig(output_dir=self.directory_with_results),
        ).run()


        from unstructured.staging.base import elements_from_json


        elements = []
        for filename in os.listdir(self.directory_with_results):
            if filename.endswith(".json"):
                file_path = os.path.join(self.directory_with_results, filename)
                try:
                    elements.extend(elements_from_json(filename=file_path))
                except IOError:
                    print(f"Error: Could not read file {filename}.")



        documents = []
        for element in elements:
            metadata = element.metadata.to_dict()
            metadata["reference"] = directory #TODO test it
            documents.append(
                Document(
                    page_content=element.text,
                    metadata=metadata,
                )
            )
        return documents
    
    @property
    def supported_file_types(self) -> List[str]:  #TODO
        return ["pdf"]