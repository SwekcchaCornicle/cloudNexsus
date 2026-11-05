from app.evaluation.metrics import evaluate_query


retrieved_ids = [
    "chunk-B",
    "chunk-A",
    "chunk-C",
]

relevant_ids = [
    "chunk-A",
]

results = evaluate_query(
    retrieved_ids=retrieved_ids,
    relevant_ids=relevant_ids,
    k=2,
)

print("\nRetrieval Evaluation")
print("=" * 45)

for metric, score in results.items():
    print(f"{metric}: {score:.4f}")