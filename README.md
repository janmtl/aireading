# 🧠 AI Research Digest

An automated nightly digest of the latest advancements in AI inference and post-training, built with LLM-powered summarization.

## Features

- **Nightly Automated Builds** - Fetches and summarizes AI research daily
- **Longitudinal View** - Track developments over time without daily checking
- **LLM-Powered Curation** - Uses Claude to identify significant breakthroughs
- **Beautiful UI** - Responsive, modern interface with dark mode support
- **Multiple Sources** - Aggregates from arXiv, research blogs, and industry announcements

## Architecture

```
┌─────────────────┐
│  Data Sources   │
│  • arXiv        │
│  • RSS Feeds    │
│  • Blogs        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Fetch & Filter  │
│ (Python)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ LLM Summary     │
│ (Claude API)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Generate HTML   │
│ (Jinja2)        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Deploy          │
│ (Amplify/Pages) │
└─────────────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Anthropic API key (or OpenAI API key)
- AWS account (for Amplify deployment) OR GitHub account (for Pages deployment)

### Local Development

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd <repo-name>
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up API key**
   ```bash
   export ANTHROPIC_API_KEY='your-api-key-here'
   ```

4. **Run the build**
   ```bash
   python generate_summary.py
   ```

5. **View the result**
   ```bash
   open public/index.html
   ```

## Configuration

Edit `config.yaml` to customize:

- **Sources**: Add/remove RSS feeds, arXiv queries
- **LLM Settings**: Change model, temperature, or provider
- **Build Settings**: Adjust lookback days, output directories
- **Filtering**: Set significance thresholds

### Example: Adding a New RSS Feed

```yaml
sources:
  rss_feeds:
    - name: "Your Blog Name"
      url: "https://yourblog.com/feed.xml"
      category: "research"
```

### Example: Changing LLM Provider

```yaml
llm:
  provider: "openai"  # Switch from anthropic to openai
  model: "gpt-4-turbo"
  temperature: 0.3
```

## Deployment Options

### Option 1: AWS Amplify (Recommended)

1. **Push your code to GitHub**

2. **Create Amplify App**
   - Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
   - Click "New app" → "Host web app"
   - Connect your GitHub repository
   - Select the branch (e.g., `main`)

3. **Configure Build Settings**
   - Amplify will auto-detect `amplify.yml`
   - Add environment variable: `ANTHROPIC_API_KEY`

4. **Set up Nightly Builds**
   - The GitHub Actions workflow will handle builds
   - Or configure Amplify's scheduled builds (Console → Build settings → Schedule)

5. **Deploy**
   - Amplify will build and deploy automatically
   - Your site will be live at: `https://[app-id].amplifyapp.com`

### Option 2: GitHub Pages

1. **Enable GitHub Actions**
   - The workflow is already configured in `.github/workflows/nightly-build.yml`

2. **Add Secrets**
   - Go to your repo → Settings → Secrets and variables → Actions
   - Add `ANTHROPIC_API_KEY`

3. **Enable GitHub Pages**
   - Settings → Pages
   - Source: Deploy from branch
   - Branch: `gh-pages`

4. **Your site will be live at**
   - `https://[username].github.io/[repo-name]/`

### Option 3: Self-Hosted (Cron Job)

```bash
# Add to crontab
0 2 * * * cd /path/to/repo && python generate_summary.py
```

## Data Storage

Generated summaries are stored in JSON format:

```
summaries/
  2026-06-30.json
  2026-06-29.json
  ...
```

Each summary contains:
- Curated items with significance scores
- Identified trends
- Metadata (model used, timestamp, etc.)

## Customizing the UI

Edit `template.html` to modify:
- Layout and styling
- Color scheme (check CSS variables in `:root`)
- Displayed information
- Add custom sections

The template uses Jinja2 syntax for dynamic content.

## Sources Included

### Research Blogs
- Hugging Face Blog
- vLLM Blog
- Modal Labs Blog
- Sebastian Raschka's Substack
- Cameron R. Wolfe's Substack

### Academic
- arXiv (cs.LG, cs.CL, cs.CV)
  - Filtered for: inference, quantization, RLHF, DPO, post-training

### Your Reading List
The project includes your existing `reading-list-draft.md` as reference material.

## Cost Estimates

### Anthropic API (Claude Sonnet 5)
- ~$0.10-0.30 per daily summary
- ~$3-10 per month
- Promotional pricing through Aug 31, 2026: $2/MTok input, $10/MTok output
- Standard pricing after: $3/MTok input, $15/MTok output

### AWS Amplify
- Free tier: 1000 build minutes/month
- Hosting: $0.15/GB stored + $0.15/GB served
- Estimated: $0-5/month for low traffic

### GitHub Pages
- Free for public repositories

## Troubleshooting

### "No items fetched"
- Check your internet connection
- Verify RSS feed URLs are still valid
- Some feeds may rate-limit; add delays in `fetch_sources.py`

### "ANTHROPIC_API_KEY not set"
- Ensure environment variable is set
- For GitHub Actions: check repo secrets
- For Amplify: check environment variables in console

### HTML not generating
- Check that `template.html` exists
- Verify Jinja2 syntax is valid
- Look for errors in console output

## Development

### Project Structure

```
.
├── config.yaml              # Configuration
├── fetch_sources.py         # Source fetching logic
├── generate_summary.py      # Main build script
├── template.html            # HTML template
├── requirements.txt         # Python dependencies
├── amplify.yml             # AWS Amplify config
├── .github/
│   └── workflows/
│       └── nightly-build.yml  # GitHub Actions workflow
├── summaries/              # Generated JSON summaries
│   └── YYYY-MM-DD.json
└── public/                 # Built HTML site
    └── index.html
```

### Running Tests

```bash
# Test source fetching
python fetch_sources.py

# Generate demo HTML with sample data (for testing UI without API calls)
python create_demo.py

# Generate real summary from live sources
python generate_summary.py
```

**Important:** If you've run `create_demo.py` for testing, delete the demo summary files before running `generate_summary.py` to avoid mixing demo and real data:

```bash
# Remove demo summaries (if they exist)
rm summaries/2026-*.json

# Then generate real summaries
python generate_summary.py
```

### Adding New Sources

1. Edit `config.yaml` to add source configuration
2. Modify `fetch_sources.py` if custom fetching logic is needed
3. Test locally before deploying

## Contributing

Feel free to customize this for your needs! Some ideas:

- Add more data sources (Twitter/X, Reddit, newsletters)
- Implement email notifications
- Add search/filter functionality
- Create API endpoints
- Add RSS feed output

## License

MIT License - feel free to use and modify as needed.

## Acknowledgments

Built with:
- [Claude](https://anthropic.com) for LLM summarization
- [Jinja2](https://jinja.palletsprojects.com/) for templating
- [feedparser](https://github.com/kurtmckee/feedparser) for RSS
- [arxiv](https://github.com/lukasschwab/arxiv.py) for paper fetching

---

**Questions?** Open an issue or customize to your heart's content!
