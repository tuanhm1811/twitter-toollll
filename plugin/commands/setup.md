---
description: Configure Social Agent API keys and preferences
argument-hint: [platform]
---

Walk the user through configuring their Social Agent project. Store config at `.social-agent.yaml` in the current directory.

## Process

1. **Check for existing config**: Read `.social-agent.yaml` in the current directory. If it exists, show current config (mask API keys — show only last 4 characters) and ask if user wants to update.

2. **If a platform argument is given** (e.g., `/setup twitter`), skip to that platform's credential collection (step 5). Only update that platform's section in the config.

3. **Collect kie.ai API key** using AskUserQuestion:
   - "Enter your kie.ai API key (for image generation, get it from https://kie.ai/api-key)."

4. **Ask which platforms to configure**:
   - "Which platforms do you want to configure? (twitter, reddit, threads, facebook — you can pick multiple, comma-separated)"

5. **For each selected platform**, collect credentials one at a time using AskUserQuestion:

   **Twitter:**
   - First show guide: "To get Twitter API credentials: 1) Go to https://developer.twitter.com/en/portal/dashboard 2) Create a project and app 3) Under 'Keys and tokens', generate API Key, API Secret, Access Token, and Access Token Secret 4) Make sure your app has Read and Write permissions"
   - Then collect: API Key, API Secret, Access Token, Access Token Secret

   **Reddit:**
   - First show guide: "To get Reddit API credentials: 1) Go to https://www.reddit.com/prefs/apps 2) Click 'create another app...' at the bottom 3) Choose 'script' type 4) Set redirect URI to http://localhost:8080 5) Note the client ID (under app name) and client secret"
   - Then collect: Client ID, Client Secret, Reddit Username, Reddit Password

   **Threads:**
   - First show guide: "To get Threads API access: 1) Go to https://developers.facebook.com/ 2) Create an app with 'Threads API' product 3) In Threads API settings, generate a long-lived access token 4) Required permissions: threads_basic, threads_content_publish"
   - Then collect: Access Token

   **Facebook:**
   - First show guide: "To get Facebook Page access: 1) Go to https://developers.facebook.com/ 2) Create an app with 'Facebook Login' product 3) Get a Page Access Token via Graph API Explorer (https://developers.facebook.com/tools/explorer/) 4) Select your Page and request pages_manage_posts permission 5) Get your Page ID from your Facebook Page's About section"
   - Then collect: Page Access Token, Page ID

6. **Collect preferences**:
   - "Should posts be published without confirmation? (yes/no, default: no)"

7. **Write config file**: Save all values to `.social-agent.yaml`. Only include platform sections that the user configured. Preserve existing sections when updating a single platform.

8. **Create project directories** if they don't exist: `knowledges/`, `contents/`, `images/`.

9. **Install Python dependencies**: Run `pip install -r ${CLAUDE_PLUGIN_ROOT}/scripts/requirements.txt`

10. **Warn about .gitignore**: If a `.gitignore` file exists, check if `.social-agent.yaml` is listed. If not, suggest adding it.

11. **Confirm**: "Setup complete! Configured platforms: [list]. Add knowledge files to ./knowledges/ or use `/import <file>` to bring in files."
