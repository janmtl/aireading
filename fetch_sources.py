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

try:
    from mastodon import Mastodon
    MASTODON_AVAILABLE = True
except ImportError:
    MASTODON_AVAILABLE = False
    print("Warning: Mastodon.py not installed. Mastodon fetching will be disabled.")


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
        
        # Fetch Hacker News stories
        if self.config.get('sources', {}).get('hackernews', {}).get('enabled', True):
            items.extend(self._fetch_hackernews())
            time.sleep(1)
        
        # Fetch Mastodon posts
        if self.config.get('sources', {}).get('mastodon', {}).get('enabled', True):
            items.extend(self._fetch_mastodon())
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
            client = arxiv.Client()
            search = arxiv.Search(
                query=query_config['query'],
                max_results=query_config.get('max_results', 10),
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            for result in client.results(search):
                # Filter by date
                pub_date = result.published.replace(tzinfo=None) if result.published.tzinfo else result.published
                if pub_date < self.cutoff_date:
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
    
    def _fetch_hackernews(self) -> List[Dict[str, Any]]:
        """Fetch top stories from Hacker News."""
        items = []
        hn_config = self.config.get('sources', {}).get('hackernews', {})
        
        if not hn_config.get('enabled', True):
            return items
        
        max_stories = hn_config.get('max_stories', 50)
        min_score = hn_config.get('min_score', 20)
        
        try:
            print(f"  Fetching Hacker News top stories...")
            
            # Fetch top story IDs
            response = requests.get('https://hacker-news.firebaseio.com/v0/topstories.json')
            response.raise_for_status()
            story_ids = response.json()[:max_stories]
            
            # Fetch individual stories
            for story_id in story_ids:
                try:
                    time.sleep(0.1)  # Be polite with rate limiting
                    response = requests.get(f'https://hacker-news.firebaseio.com/v0/item/{story_id}.json')
                    response.raise_for_status()
                    story = response.json()
                    
                    if not story or story.get('type') != 'story':
                        continue
                    
                    score = story.get('score', 0)
                    if score < min_score:
                        continue
                    
                    # Parse timestamp
                    pub_date = datetime.fromtimestamp(story.get('time', 0))
                    
                    # Filter by date
                    if pub_date < self.cutoff_date:
                        continue
                    
                    comments = story.get('descendants', 0)
                    title = story.get('title', 'Untitled')
                    url = story.get('url', f"https://news.ycombinator.com/item?id={story_id}")
                    
                    item = {
                        'title': title,
                        'url': url,
                        'summary': f"HN discussion with {score} points, {comments} comments",
                        'published': pub_date.isoformat(),
                        'source': 'Hacker News',
                        'category': 'community',
                        'type': 'discussion',
                        'score': score,
                        'comments': comments
                    }
                    items.append(item)
                
                except Exception as e:
                    print(f"    Error fetching HN story {story_id}: {e}")
                    continue
            
            print(f"    Fetched {len(items)} HN stories")
        
        except Exception as e:
            print(f"    Error fetching Hacker News: {e}")
        
        return items
    
    def _fetch_mastodon(self) -> List[Dict[str, Any]]:
        """Fetch posts from Mastodon instance via hashtags."""
        items = []
        
        if not MASTODON_AVAILABLE:
            print("  Mastodon.py not available, skipping Mastodon fetching")
            return items
        
        mastodon_config = self.config.get('sources', {}).get('mastodon', {})
        
        if not mastodon_config.get('enabled', True):
            return items
        
        instance = mastodon_config.get('instance', 'https://sigmoid.social')
        hashtags = mastodon_config.get('hashtags', [])
        lookback_hours = mastodon_config.get('lookback_hours', 168)
        max_posts_per_tag = mastodon_config.get('max_posts_per_tag', 30)
        
        if not hashtags:
            return items
        
        try:
            print(f"  Fetching Mastodon posts from {instance}...")
            
            # Connect to instance (no auth needed for public timeline search)
            mastodon = Mastodon(api_base_url=instance)
            
            cutoff_time = datetime.now() - timedelta(hours=lookback_hours)
            seen_urls = set()  # Deduplicate posts
            
            for hashtag in hashtags:
                try:
                    print(f"    Searching hashtag: #{hashtag}")
                    
                    # Search for hashtag
                    results = mastodon.timeline_hashtag(
                        hashtag,
                        limit=max_posts_per_tag
                    )
                    
                    for post in results:
                        # Parse timestamp
                        pub_date = post['created_at']
                        if pub_date.tzinfo:
                            pub_date = pub_date.replace(tzinfo=None)
                        
                        # Filter by date
                        if pub_date < cutoff_time:
                            continue
                        
                        post_url = post['url']
                        
                        # Skip duplicates
                        if post_url in seen_urls:
                            continue
                        seen_urls.add(post_url)
                        
                        # Extract content
                        content = post.get('content', '')
                        # Strip HTML tags for summary
                        from bs4 import BeautifulSoup
                        clean_content = BeautifulSoup(content, 'html.parser').get_text()
                        
                        author = post['account']['username']
                        title_preview = clean_content[:100].replace('\n', ' ').strip()
                        if len(clean_content) > 100:
                            title_preview += '...'
                        
                        item = {
                            'title': f"Post by @{author}: {title_preview}",
                            'url': post_url,
                            'summary': clean_content,
                            'published': pub_date.isoformat(),
                            'source': 'Mastodon (sigmoid.social)',
                            'category': 'social',
                            'type': 'post',
                            'author': f"@{author}",
                            'engagement': {
                                'boosts': post.get('reblogs_count', 0),
                                'favorites': post.get('favourites_count', 0)
                            }
                        }
                        items.append(item)
                    
                    time.sleep(1)  # Be polite between hashtag searches
                
                except Exception as e:
                    print(f"    Error fetching hashtag #{hashtag}: {e}")
                    continue
            
            print(f"    Fetched {len(items)} Mastodon posts")
        
        except Exception as e:
            print(f"    Error fetching Mastodon: {e}")
        
        return items


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
