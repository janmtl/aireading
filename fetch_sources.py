#!/usr/bin/env python3
"""
Fetch content from various AI research sources.
"""

import feedparser
import arxiv
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any
import time


class SourceFetcher:
    """Fetches content from RSS feeds, arXiv, and other sources."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.lookback_days = config.get('build', {}).get('lookback_days', 7)
        self.cutoff_date = datetime.now() - timedelta(days=self.lookback_days)
    
    def fetch_all(self) -> List[Dict[str, Any]]:
        """Fetch from all configured sources."""
        items = []
        
        print(f"Fetching sources (looking back {self.lookback_days} days)...")
        
        # Fetch RSS feeds
        for feed_config in self.config.get('sources', {}).get('rss_feeds', []):
            print(f"  Fetching: {feed_config['name']}")
            items.extend(self._fetch_rss(feed_config))
            time.sleep(1)  # Be polite
        
        # Fetch arXiv papers
        for query_config in self.config.get('sources', {}).get('arxiv_queries', []):
            print(f"  Fetching arXiv: {query_config['query'][:50]}...")
            items.extend(self._fetch_arxiv(query_config))
            time.sleep(1)
        
        print(f"Total items fetched: {len(items)}")
        return items
    
    def _fetch_rss(self, feed_config: Dict[str, str]) -> List[Dict[str, Any]]:
        """Fetch items from an RSS feed."""
        items = []
        
        try:
            feed = feedparser.parse(feed_config['url'])
            
            for entry in feed.entries:
                # Parse published date
                pub_date = None
                if hasattr(entry, 'published_parsed'):
                    pub_date = datetime(*entry.published_parsed[:6])
                elif hasattr(entry, 'updated_parsed'):
                    pub_date = datetime(*entry.updated_parsed[:6])
                
                # Filter by date
                if pub_date and pub_date < self.cutoff_date:
                    continue
                
                item = {
                    'title': entry.get('title', 'Untitled'),
                    'url': entry.get('link', ''),
                    'summary': entry.get('summary', entry.get('description', '')),
                    'published': pub_date.isoformat() if pub_date else datetime.now().isoformat(),
                    'source': feed_config['name'],
                    'category': feed_config.get('category', 'general'),
                    'type': 'blog'
                }
                items.append(item)
        
        except Exception as e:
            print(f"    Error fetching {feed_config['name']}: {e}")
        
        return items
    
    def _fetch_arxiv(self, query_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch papers from arXiv."""
        items = []
        
        try:
            search = arxiv.Search(
                query=query_config['query'],
                max_results=query_config.get('max_results', 10),
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            for result in search.results():
                # Filter by date
                if result.published < self.cutoff_date:
                    continue
                
                item = {
                    'title': result.title,
                    'url': result.entry_id,
                    'summary': result.summary,
                    'published': result.published.isoformat(),
                    'source': 'arXiv',
                    'category': query_config.get('category', 'research'),
                    'type': 'paper',
                    'authors': [author.name for author in result.authors]
                }
                items.append(item)
        
        except Exception as e:
            print(f"    Error fetching arXiv: {e}")
        
        return items
    
    def _fetch_github_trending(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch trending GitHub repositories (placeholder - requires scraping)."""
        # Note: GitHub doesn't have an official trending API
        # This would require scraping or using a third-party service
        # Leaving as placeholder for now
        return []


def main():
    """Test the fetcher."""
    import yaml
    
    with open('config.yaml', 'r') as f:
        config = yaml.safe_load(f)
    
    fetcher = SourceFetcher(config)
    items = fetcher.fetch_all()
    
    print(f"\nFetched {len(items)} items")
    for item in items[:3]:
        print(f"  - {item['title'][:60]}... ({item['source']})")


if __name__ == '__main__':
    main()
