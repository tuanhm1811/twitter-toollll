---
description: Initialize current directory as a Social Agent project
---

Initialize the current working directory as a Social Agent project.

## Process

1. Check if `./knowledges/`, `./contents/`, and `./images/` directories already exist. If all exist, tell user: "Project already initialized."

2. Create directories:
   - `./knowledges/` — for imported knowledge files
   - `./contents/` — for generated social media content (.md drafts)
   - `./images/` — for generated images (banners, etc.)

3. Show the expected project structure:
   ```
   project/
   ├── .social-agent.yaml     # Config (run /setup)
   ├── knowledges/             # Knowledge files
   ├── contents/               # Content drafts (Twitter, Reddit, Threads, Facebook)
   ├── images/                 # Generated images
   └── summary.md              # Knowledge summary
   ```

4. Check if `.social-agent.yaml` exists in the current directory. If not, suggest: "Run `/setup` to configure your API keys."

5. Confirm: "Project initialized. Add knowledge files to ./knowledges/ or use `/import <file>` to bring in files and URLs."
