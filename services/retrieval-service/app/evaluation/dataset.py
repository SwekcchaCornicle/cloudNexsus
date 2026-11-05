"""
CloudNexus multi-cloud retrieval evaluation dataset.

Relevant chunk IDs are manually labelled using the
actual content stored in Neo4j.
"""

EVALUATION_DATASET = [

    # AWS questions
    {
        "id": "aws_event_source_mapping",
        "question": "What is an event source mapping in AWS Lambda?",
        "provider": "AWS",
        "service_name": "Lambda",
        "relevant_chunk_ids": [
            "e5159663-f865-4a83-8ffe-b432ee8df87e:00001"
        ],
    },
    {
        "id": "aws_lambda_definition",
        "question": "What is AWS Lambda?",
        "provider": "AWS",
        "service_name": "Lambda",
        "relevant_chunk_ids": [
            "e5159663-f865-4a83-8ffe-b432ee8df87e:00000"
        ],
    },

    # Azure questions
    {
        "id": "azure_functions_definition",
        "question": "What is Azure Functions?",
        "provider": "AZURE",
        "service_name": "azure_function",
        "relevant_chunk_ids": [
            "85d639fb-d7ef-48fb-b650-616c4149686d:00000"
        ],
    },
    {
        "id": "azure_triggers",
        "question": "What causes an Azure Function to run?",
        "provider": "AZURE",
        "service_name": "azure_function",
        "relevant_chunk_ids": [
            "85d639fb-d7ef-48fb-b650-616c4149686d:00000"
        ],
    },

    # GCP questions
    {
        "id": "gcp_cloud_run_functions",
        "question": "What are Cloud Run functions?",
        "provider": "GCP",
        "service_name": "gcp_function",
        "relevant_chunk_ids": [
            "235a6622-12ce-4efb-a4af-ac2685a13a1f:00000"
        ],
    },
    {
        "id": "gcp_event_sources",
        "question": "How do Google Cloud functions respond to events?",
        "provider": "GCP",
        "service_name": "gcp_function",
        "relevant_chunk_ids": [
            "235a6622-12ce-4efb-a4af-ac2685a13a1f:00000"
        ],
    },
]