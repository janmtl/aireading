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

I will provide you with a list of recent articles, blog posts, and papers.

CRITICAL JSON FORMAT REQUIREMENTS:
1. Your ENTIRE response must be valid JSON - no text before or after
2. Use ONLY double quotes for JSON strings (never single quotes)
3. Keep descriptions SHORT (under 80 characters) to avoid formatting issues
4. Do NOT include literal newlines, tabs, or control characters in strings
5. Escape special characters: use \" for quotes, \\ for backslashes
6. If uncertain about special characters, omit them or use simple punctuation

Response schema (return ONLY this JSON, nothing else):
{
  "items": [
    {
      "title": "string (original title)",
      "url": "string (source URL)",
      "core_innovation": "string (what is new - max 60 chars)",
      "significance": "string (why it matters - max 60 chars)",
      "practical_readiness": "string (one of: research, prototype, production-ready)",
      "significance_score": 0.8,
      "category": "string (one of: inference, post-training, architecture, tooling, research)"
    }
  ],
  "trends": ["string (max 70 chars)", "string (max 70 chars)"],
  "summary": "Brief 2-3 sentence overview of key developments"
}

Prioritize signal over noise. Omit items that are:
- Marginal improvements on existing methods
- Single-dataset optimizations without broader applicability
- Purely theoretical without experimental validation
- Marketing content without technical substance

Remember: Output ONLY valid JSON. No markdown code blocks, no explanations, just the JSON object.

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
                
                # Save the problematic response for debugging
                debug_file = f"debug_response_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                with open(debug_file, "w") as f:
                    f.write(response_text)
                print(f"  Raw response saved to {debug_file}")
                
                # Try multiple repair strategies
                import re
                fixed_text = response_text
                
                # Strategy 1: Remove control characters and fix escaped quotes
                fixed_text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', fixed_text)
                
                # Strategy 2: Fix common escaping issues in strings
                # Replace unescaped newlines within JSON string values
                fixed_text = re.sub(r'(?<!\\)\\n', ' ', fixed_text)
                fixed_text = re.sub(r'(?<!\\)\\t', ' ', fixed_text)
                
                # Strategy 3: Try to repair unterminated strings by finding the last valid position
                # This is a heuristic approach - look for common JSON structure markers
                if e.msg.startswith("Unterminated string"):
                    # Try to find where the JSON structure broke
                    # Look for the last occurrence of valid JSON markers before the error position
                    error_pos = e.pos if hasattr(e, 'pos') else len(fixed_text)
                    # Try truncating at various positions and adding closing structures
                    for search_back in [0, 100, 200, 500]:
                        truncate_pos = max(0, error_pos - search_back)
                        test_text = fixed_text[:truncate_pos]
                        # Try adding closing quotes and braces
                        for ending in ['"}]}', '"],"trends":[],"summary":"Partial response due to parsing error"}',
                                      '"}],"trends":[],"summary":"Partial response"}']:
                            try:
                                summary_data = json.loads(test_text + ending)
                                print(f"  Successfully repaired JSON by truncating and adding closure")
                                break
                            except json.JSONDecodeError:
                                continue
                        if 'summary_data' in locals():
                            break
                
                # If we haven't succeeded with repair strategies, try the cleaned text
                if 'summary_data' not in locals():
                    try:
                        summary_data = json.loads(fixed_text)
                        print(f"  Successfully parsed after cleaning control characters")
                    except json.JSONDecodeError as e2:
                        # Last resort: return a minimal valid structure
                        print(f"  Could not repair JSON. Returning minimal structure.")
                        summary_data = {
                            "items": [],
                            "trends": ["JSON parsing error - manual review needed"],
                            "summary": f"Failed to parse LLM response. Error: {e2}. Check {debug_file}",
                            "parsing_error": True
                        }
            
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
