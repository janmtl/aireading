# Quick Start Guide

## Initial Setup (5 minutes)

### 1. Get an API Key

You'll need either:
- **Anthropic API key** (recommended): https://console.anthropic.com/
  - Sign up and get $5 free credit
- **OpenAI API key**: https://platform.openai.com/

### 2. Local Testing

```bash
# Install dependencies
pip install -r requirements.txt

# Set your API key
export ANTHROPIC_API_KEY='sk-ant-...'

# Generate demo (no API calls)
python create_demo.py

# Open the result
open public/index.html  # Mac
# or
xdg-open public/index.html  # Linux
# or just open public/index.html in your browser
```

### 3. Real Build (uses API)

```bash
# This will fetch real data and use the LLM
python generate_summary.py

# View the result
open public/index.html
```

## Deployment Options

### Option A: GitHub Actions (Easiest)

1. Push this code to GitHub
2. Go to repo Settings → Secrets → Actions
3. Add secret: `ANTHROPIC_API_KEY` with your key
4. The workflow will run nightly at 2 AM UTC
5. View results at: `https://[username].github.io/[repo-name]/`

### Option B: AWS Amplify

1. Push code to GitHub
2. Go to [AWS Amplify Console](https://console.aws.amazon.com/amplify/)
3. Click "New app" → "Host web app"
4. Connect your GitHub repo
5. Add environment variable: `ANTHROPIC_API_KEY`
6. Amplify will build and deploy automatically

## Configuration

Edit `config.yaml` to:
- Add/remove sources
- Change LLM model
- Adjust lookback days
- Set significance thresholds

## Cost Estimate

- **Anthropic Claude Sonnet 5**: ~$0.15 per daily run
- **Monthly cost**: ~$5-7
- **AWS Amplify**: Free tier covers most use cases

## Troubleshooting

**No items fetched?**
- Some RSS feeds may be slow or rate-limited
- Check your internet connection

**API errors?**
- Verify your API key is set correctly
- Check you have API credits remaining

**HTML looks broken?**
- Try running `create_demo.py` first to verify setup
- Check that all dependencies installed correctly

## Next Steps

1. Customize the sources in `config.yaml`
2. Adjust the LLM prompt in `generate_summary.py`
3. Modify the HTML template for your preferred look
4. Set up automated deployment

**Questions?** Check the full README.md
