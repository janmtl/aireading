#!/usr/bin/env python3
"""
Create a demo summary for testing the HTML output without calling the API.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from generate_summary import load_recent_summaries, generate_html


def create_demo_summaries():
    """Create demo summary files for testing."""
    Path("summaries").mkdir(exist_ok=True)
    
    demo_summaries = [
        {
            "date": (datetime.now() - timedelta(days=0)).strftime("%Y-%m-%d"),
            "summary": "This week saw major advances in inference optimization with new quantization techniques and breakthrough improvements in reasoning models. The focus is shifting toward practical deployment at scale.",
            "items": [
                {
                    "title": "BitNet 4.0: 1-bit LLMs Reach GPT-4 Performance",
                    "url": "https://arxiv.org/abs/2606.example1",
                    "core_innovation": "Achieves competitive performance with GPT-4 using only 1-bit weights through novel training techniques and architectural modifications.",
                    "significance": "Could reduce inference costs by 10-20x while maintaining quality, making large models accessible for edge deployment.",
                    "practical_readiness": "prototype",
                    "significance_score": 0.95,
                    "category": "inference"
                },
                {
                    "title": "Gemini 2.0 Pro: Native Tool Use and Multi-Modal Reasoning",
                    "url": "https://blog.google/technology/ai/gemini-2-release",
                    "core_innovation": "First production model with native tool calling trained end-to-end, plus real-time video understanding capabilities.",
                    "significance": "Eliminates complex prompt engineering for tool use and enables new classes of interactive AI applications.",
                    "practical_readiness": "production-ready",
                    "significance_score": 0.92,
                    "category": "post-training"
                },
                {
                    "title": "vLLM 0.8: Speculative Decoding with 2x Speedup",
                    "url": "https://blog.vllm.ai/2026/06/speculative-decoding",
                    "core_innovation": "Production-ready speculative decoding with automatic draft model selection and dynamic batch size adjustment.",
                    "significance": "Doubles inference throughput for many workloads without accuracy loss, immediately applicable to existing deployments.",
                    "practical_readiness": "production-ready",
                    "significance_score": 0.88,
                    "category": "inference"
                },
                {
                    "title": "Constitutional AI at Scale: Training LLMs with 10M Examples",
                    "url": "https://www.anthropic.com/research/constitutional-ai-scale",
                    "core_innovation": "Demonstrates that constitutional AI methods scale effectively to massive datasets, improving both safety and capabilities.",
                    "significance": "Provides a clear path for aligning increasingly powerful models without human preference data bottlenecks.",
                    "practical_readiness": "research",
                    "significance_score": 0.85,
                    "category": "post-training"
                }
            ],
            "trends": [
                "Quantization techniques achieving near-zero quality loss",
                "Production systems adopting speculative decoding",
                "Multi-modal models becoming standard, not specialized",
                "Tool use moving from prompt engineering to native training"
            ],
            "generated_at": datetime.now().isoformat(),
            "model": "claude-sonnet-5",
            "total_items_analyzed": 47
        },
        {
            "date": (datetime.now() - timedelta(days=3)).strftime("%Y-%m-%d"),
            "summary": "Major focus on RLHF alternatives and synthetic data generation. Multiple papers showing DPO variants outperforming traditional RLHF with lower computational costs.",
            "items": [
                {
                    "title": "DPO++: Fixing Distribution Mismatch in Direct Preference Optimization",
                    "url": "https://arxiv.org/abs/2606.example2",
                    "core_innovation": "Addresses key weakness in DPO where the reference model distribution diverges, leading to more stable training.",
                    "significance": "Makes DPO more reliable for production use, potentially replacing RLHF as the default post-training method.",
                    "practical_readiness": "prototype",
                    "significance_score": 0.82,
                    "category": "post-training"
                },
                {
                    "title": "Synthetic Data for Math Reasoning: Quality Over Quantity",
                    "url": "https://arxiv.org/abs/2606.example3",
                    "core_innovation": "Shows that 10K high-quality synthetic math problems outperform 100K scraped problems when properly filtered.",
                    "significance": "Challenges the scaling paradigm and suggests we need better data curation, not just more data.",
                    "practical_readiness": "research",
                    "significance_score": 0.78,
                    "category": "post-training"
                }
            ],
            "trends": [
                "DPO variants gaining momentum over traditional RLHF",
                "Synthetic data quality becoming more important than scale",
                "Focus on data efficiency rather than pure scaling"
            ],
            "generated_at": (datetime.now() - timedelta(days=3)).isoformat(),
            "model": "claude-sonnet-5",
            "total_items_analyzed": 39
        },
        {
            "date": (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d"),
            "summary": "Inference optimization continues to dominate with new frameworks and techniques. Several breakthroughs in long-context handling and memory efficiency.",
            "items": [
                {
                    "title": "Infinite-Context Transformers: O(1) Memory for Any Sequence Length",
                    "url": "https://arxiv.org/abs/2606.example4",
                    "core_innovation": "Uses hierarchical compression to maintain constant memory while processing arbitrarily long sequences.",
                    "significance": "Removes a fundamental limitation of transformers, enabling new applications in long-form content.",
                    "practical_readiness": "research",
                    "significance_score": 0.91,
                    "category": "architecture"
                }
            ],
            "trends": [
                "Long-context methods moving toward production",
                "Memory efficiency becoming as important as speed"
            ],
            "generated_at": (datetime.now() - timedelta(days=7)).isoformat(),
            "model": "claude-sonnet-5",
            "total_items_analyzed": 42
        }
    ]
    
    # Save each summary
    for summary in demo_summaries:
        filepath = Path("summaries") / f"{summary['date']}.json"
        with open(filepath, 'w') as f:
            json.dump(summary, f, indent=2)
        print(f"Created demo summary: {filepath}")
    
    return demo_summaries


def main():
    """Generate demo HTML."""
    print("Creating demo summaries...")
    create_demo_summaries()
    
    print("\nGenerating HTML from demo data...")
    summaries = load_recent_summaries("summaries", days=30)
    generate_html(summaries, "public")
    
    print("\n✅ Demo generated successfully!")
    print("Open public/index.html in your browser to see the result.")


if __name__ == '__main__':
    main()
