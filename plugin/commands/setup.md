---
description: Configure Twitter Agent API keys and preferences
---

Walk the user through configuring their Twitter Agent project. Store config at `.twitter-agent.yaml` in the current directory.

## Process

1. **Check for existing config**: Read `.twitter-agent.yaml` in the current directory. If it exists, show current config (mask API keys — show only last 4 characters) and ask if user wants to update.

2. **Collect API keys one at a time** using AskUserQuestion:

   a. **kie.ai API key**: "Enter your kie.ai API key (for image generation, get it from https://kie.ai/api-key)."

   b. **Twitter API Key**: "Enter your Twitter API key (from developer.twitter.com)."

   c. **Twitter API Secret**: "Enter your Twitter API secret."

   d. **Twitter Access Token**: "Enter your Twitter access token."

   e. **Twitter Access Token Secret**: "Enter your Twitter access token secret."

3. **Collect preferences**:

   a. **Auto post**: "Should tweets be posted without confirmation? (yes/no, default: no)"

4. **Write config file**: Save all values to `.twitter-agent.yaml` in the current directory as plain YAML:

```yaml
kie_api_key: <value>
twitter_api_key: <value>
twitter_api_secret: <value>
twitter_access_token: <value>
twitter_access_secret: <value>
auto_post: <value>
```

5. **Create project directories** if they don't exist: `knowledges/`, `contents/`, `images/`.

6. **Install Python dependencies**: Run `pip install -r ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.txt`

7. **Warn about .gitignore**: If a `.gitignore` file exists, check if `.twitter-agent.yaml` is listed. If not, suggest adding it: "Consider adding `.twitter-agent.yaml` to your .gitignore to avoid committing API keys."

8. **Confirm**: "Setup complete! Your Twitter Agent project is ready. Add knowledge files to ./knowledges/ or use `/import <file>` to bring in files."
