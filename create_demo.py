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
                    "title": "The Era of 1-bit LLMs: All Large Language Models are in 1.58 Bits",
                    "url": "https://arxiv.org/abs/2402.17764",
                    "core_innovation": "Introduces 1.58-bit quantization that matches full precision Transformer LLM performance",
                    "significance": "Could reduce inference costs by 10-20x while maintaining quality, making large models accessible for edge deployment.",
                    "practical_readiness": "prototype",
                    "significance_score": 0.95,
                    "category": "inference"
                },
                {
                    "title": "vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention",
                    "url": "https://blog.vllm.ai/2023/06/20/vllm.html",
                    "core_innovation": "PagedAttention manages attention key-value memory efficiently for high-throughput serving",
                    "significance": "Enables 24x higher throughput than traditional methods, making LLM serving more practical at scale.",
                    "practical_readiness": "production-ready",
                    "significance_score": 0.92,
                    "category": "inference"
                },
                {
                    "title": "Direct Preference Optimization: Your Language Model is Secretly a Reward Model",
                    "url": "https://arxiv.org/abs/2305.18290",
                    "core_innovation": "Eliminates need for separate reward model by optimizing policy directly from preferences",
                    "significance": "Simplifies RLHF pipeline and reduces computational costs while improving alignment quality.",
                    "practical_readiness": "production-ready",
                    "significance_score": 0.88,
                    "category": "post-training"
                },
                {
                    "title": "Constitutional AI: Harmlessness from AI Feedback",
                    "url": "https://arxiv.org/abs/2212.08073",
                    "core_innovation": "Trains AI systems using AI-generated feedback guided by constitutional principles",
                    "significance": "Provides a scalable path for aligning increasingly powerful models without human preference data bottlenecks.",
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
                    "title": "RLAIF: Scaling Reinforcement Learning from Human Feedback with AI Feedback",
                    "url": "https://arxiv.org/abs/2309.00267",
                    "core_innovation": "Demonstrates that AI-generated preferences can match human preferences for RLHF",
                    "significance": "Makes DPO more reliable for production use by addressing the data bottleneck in RLHF.",
                    "practical_readiness": "prototype",
                    "significance_score": 0.82,
                    "category": "post-training"
                },
                {
                    "title": "Textbooks Are All You Need II: phi-1.5 technical report",
                    "url": "https://arxiv.org/abs/2309.05463",
                    "core_innovation": "Shows that 1.3B model trained on high-quality synthetic data can match larger models",
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
                    "title": "Efficient Streaming Language Models with Attention Sinks",
                    "url": "https://arxiv.org/abs/2309.17453",
                    "core_innovation": "Enables LLMs to handle infinite sequence lengths by keeping attention sink tokens",
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
