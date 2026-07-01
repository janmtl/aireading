#!/usr/bin/env python3
"""
Generate AI research summaries using LLM.
"""

import os
import json
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any
import anthropic
from jinja2 import Template
from fetch_sources import SourceFetcher


SUMMARIZATION_PROMPT = """You are an AI research curator creating a digest of advancements in AI inference and post-training methods.

Your audience is an ML practitioner who checks this summary periodically (not daily), so focus on:
1. **Breakthrough developments** - not incremental improvements
2. **Practical applicability** - techniques that could be deployed soon
3. **Trend identification** - recurring themes across multiple papers/posts
4. **Longitudinal context** - how today's developments build on or diverge from recent work

I will provide you with a list of recent articles, blog posts, and papers. For each significant advancement, analyze and structure your response as JSON.

For each item worth including, provide:
- title: The original title
- url: The source URL
- core_innovation: 1-2 sentences on what's genuinely new
- significance: Why it matters for inference/post-training (1-2 sentences)
- practical_readiness: One of ["research", "prototype", "production-ready"]
- significance_score: A float from 0.0 to 1.0 indicating importance
- category: One of ["inference", "post-training", "architecture", "tooling", "research"]

Prioritize signal over noise. Omit items that are:
- Marginal improvements on existing methods
- Single-dataset optimizations without broader applicability
- Purely theoretical without experimental validation
- Marketing content without technical substance

IMPORTANT: Respond with valid, properly escaped JSON. Ensure all strings are properly quoted and escaped.
Do not include any text outside the JSON structure.

Respond with valid JSON in this format:
{
  "items": [
    {
      "title": "...",
      "url": "...",
      "core_innovation": "...",
      "significance": "...",
      "practical_readiness": "...",
      "significance_score": 0.8,
      "category": "..."
    }
  ],
  "trends": [
    "Trend 1 description",
    "Trend 2 description"
  ],
  "summary": "A brief 2-3 sentence overview of the week's developments"
}

Here are the items to analyze:

"""


class SummaryGenerator:
    """Generate summaries using an LLM."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        llm_config = config.get('llm', {})
        self.provider = llm_config.get('provider', 'anthropic')
        self.model = llm_config.get('model', 'claude-3-5-sonnet-20241022')
        self.temperature = llm_config.get('temperature', 0.3)
        self.max_tokens = llm_config.get('max_tokens', 4000)
        
        # Initialize API client
        if self.provider == 'anthropic':
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY environment variable not set")
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def generate_summary(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary from fetched items."""
        print(f"Generating summary from {len(items)} items using {self.model}...")
        
        # Prepare items for the prompt
        items_text = self._format_items_for_prompt(items)
        
        # Call LLM
        try:
            # claude-sonnet-5 doesn't support custom sampling parameters
            api_params = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [{
                    "role": "user",
                    "content": SUMMARIZATION_PROMPT + items_text
                }]
            }
            
            # Only add temperature for models that support it
            if not self.model.startswith("claude-sonnet-5"):
                api_params["temperature"] = self.temperature
            
            message = self.client.messages.create(**api_params)
            
            # Extract text from response
            # Claude Sonnet 5 has adaptive thinking enabled, so we need to find the TextBlock
            response_text = ""
            for block in message.content:
                if hasattr(block, 'text'):
                    response_text += block.text
            
            if not response_text:
                raise ValueError("No text content found in response")
            
            # Parse JSON response
            # Handle potential markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0].strip()
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0].strip()
            
            # Try to parse JSON, with fallback for common issues
            try:
                summary_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                print(f"  JSON parsing error: {e}")
                print(f"  Attempting to fix common JSON issues...")
                
                # Try to fix common issues: unescaped newlines and quotes in strings
                import re
                # This is a simple fix - for production, might need more robust handling
                fixed_text = response_text
                
                # Try parsing the fixed version
                try:
                    summary_data = json.loads(fixed_text)
                    print(f"  Successfully parsed after cleaning")
                except json.JSONDecodeError as e2:
                    print(f"  Could not fix JSON. Saving raw response for debugging.")
                    # Save the problematic response
                    with open("debug_response.txt", "w") as f:
                        f.write(response_text)
                    raise ValueError(f"Failed to parse JSON response. Error: {e2}. Raw response saved to debug_response.txt")
            
            # Add metadata
            summary_data['generated_at'] = datetime.now().isoformat()
            summary_data['model'] = self.model
            summary_data['total_items_analyzed'] = len(items)
            
            print(f"  Generated summary with {len(summary_data.get('items', []))} significant items")
            print(f"  Identified {len(summary_data.get('trends', []))} trends")
            
            return summary_data
        
        except Exception as e:
            print(f"Error generating summary: {e}")
            raise
    
    def _format_items_for_prompt(self, items: List[Dict[str, Any]]) -> str:
        """Format items for the LLM prompt."""
        formatted = []
        
        for idx, item in enumerate(items, 1):
            formatted.append(f"""
Item {idx}:
Title: {item['title']}
URL: {item['url']}
Source: {item['source']}
Published: {item['published']}
Summary: {item['summary'][:500]}...
Category: {item['category']}
Type: {item['type']}
""")
        
        return "\n".join(formatted)


def save_summary(summary: Dict[str, Any], output_dir: str):
    """Save summary to JSON file."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y-%m-%d")
    filepath = Path(output_dir) / f"{date_str}.json"
    
    with open(filepath, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Summary saved to {filepath}")
    return filepath


def load_recent_summaries(summary_dir: str, days: int = 30) -> List[Dict[str, Any]]:
    """Load recent summaries for the HTML page."""
    summary_path = Path(summary_dir)
    if not summary_path.exists():
        return []
    
    summaries = []
    cutoff = datetime.now() - timedelta(days=days)
    
    for filepath in sorted(summary_path.glob("*.json"), reverse=True):
        try:
            # Extract date from filename
            date_str = filepath.stem
            file_date = datetime.strptime(date_str, "%Y-%m-%d")
            
            if file_date < cutoff:
                continue
            
            with open(filepath, 'r') as f:
                data = json.load(f)
                data['date'] = date_str
                summaries.append(data)
        
        except Exception as e:
            print(f"Error loading {filepath}: {e}")
    
    return summaries


def generate_html(summaries: List[Dict[str, Any]], output_dir: str):
    """Generate the HTML page from summaries."""
    template_path = Path("template.html")
    
    if not template_path.exists():
        print("Warning: template.html not found, skipping HTML generation")
        return
    
    with open(template_path, 'r') as f:
        template = Template(f.read())
    
    # Prepare data for template
    latest_summary = summaries[0] if summaries else None
    
    # Calculate weekly highlights (last 7 days)
    week_ago = datetime.now() - timedelta(days=7)
    weekly_items = []
    for summary in summaries:
        if datetime.strptime(summary['date'], "%Y-%m-%d") >= week_ago:
            weekly_items.extend(summary.get('items', []))
    
    # Sort by significance score
    weekly_items.sort(key=lambda x: x.get('significance_score', 0), reverse=True)
    
    # Aggregate trends
    all_trends = []
    for summary in summaries[:7]:  # Last 7 days
        all_trends.extend(summary.get('trends', []))
    
    html_content = template.render(
        latest_summary=latest_summary,
        weekly_items=weekly_items[:10],  # Top 10
        all_summaries=summaries,
        all_trends=list(set(all_trends)),
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M UTC")
    )
    
    # Save HTML
    output_path = Path(output_dir) / "index.html"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write(html_content)
    
    print(f"HTML generated at {output_path}")


def main():
    """Main execution."""
    # Load configuration
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    # Fetch sources
    fetcher = SourceFetcher(config)
    items = fetcher.fetch_all()
    
    if not items:
        print("No items fetched, exiting")
        return
    
    # Generate summary
    generator = SummaryGenerator(config)
    summary = generator.generate_summary(items)
    
    # Save summary
    summary_dir = config.get('build', {}).get('summary_storage', 'summaries/')
    save_summary(summary, summary_dir)
    
    # Load recent summaries and generate HTML
    summaries = load_recent_summaries(summary_dir, days=30)
    output_dir = config.get('build', {}).get('output_dir', 'public/')
    generate_html(summaries, output_dir)
    
    print("\nBuild complete!")


if __name__ == '__main__':
    main()
