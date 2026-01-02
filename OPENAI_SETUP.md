# OpenAI API Configuration

## ✅ Setup Complete

The OpenAI API key has been added to your `.env` file.

## Environment Variable

```env
OPENAI_API_KEY=your-openai-api-key-here
```

## Usage in Code

To use the OpenAI API key in your Python code:

```python
import os
from dotenv import load_dotenv

load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")

# Example with OpenAI Python library
import openai
openai.api_key = openai_api_key
```

Or with the newer OpenAI client:

```python
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
```

## Security Notes

- ✅ The `.env` file is in `.gitignore` and will not be committed
- ✅ Never commit API keys to version control
- ✅ Rotate keys if they are ever exposed
- ✅ Use environment variables in production deployments

## Installing OpenAI Library

If you need to use OpenAI in your code, install the library:

```bash
pip install openai
```

Add to `requirements.txt`:
```
openai>=1.0.0
```

## Current AI Models

The codebase currently uses:
- Scikit-learn for ML-based bias detection
- Statistical analysis for bias detection
- No OpenAI integration yet (but key is ready for future use)

## Future Integration Ideas

The OpenAI API key can be used for:
- Natural language processing of evaluation feedback
- AI-powered nomination suggestions
- Advanced bias detection using LLMs
- Automated report generation
- Sentiment analysis of comments
