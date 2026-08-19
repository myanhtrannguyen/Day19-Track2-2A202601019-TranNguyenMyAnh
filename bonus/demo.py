"""Run the five required bonus queries without an LLM or external service."""
from __future__ import annotations

from agent import HybridMemoryAgent


def main() -> None:
    agent = HybridMemoryAgent()
    for memory in (
        "Tôi đã đọc Kubernetes: deployment, service, autoscaling HPA và cách theo dõi cluster.",
        "Ghi chú cloud security: dùng IAM least privilege, secret rotation, network policy và audit log.",
        "Tài liệu về autoscaling hạ tầng theo lưu lượng: đặt metric CPU và queue depth để scale out.",
        "Bài viết recommend: so sánh managed Kubernetes với serverless cho team nhỏ.",
        "Tôi quan tâm chi phí cloud: rightsizing VM, reserved instance và theo dõi egress.",
    ):
        agent.remember(memory)

    queries = [
        "Tôi đã đọc gì về Kubernetes?",
        "Recommend đọc gì tiếp",
        "Tôi đang quan tâm gì gần đây?",
        "Tài liệu về tự động mở rộng hạ tầng?",
        "Cho tôi summary cloud security",
    ]
    for i, query in enumerate(queries, start=1):
        print(f"\n=== Query {i}: {query} ===")
        print(agent.recall(query))


if __name__ == "__main__":
    main()
