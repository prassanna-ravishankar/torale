# Update Changelog Command

You are a changelog update specialist. Your task is to update the changelog with recent commits.

## Instructions

1. **Analyze recent commits**:
   - Read `frontend/public/changelog.json` to find the most recent entry date
   - Use `git log --since="<last-date>" --format="%H|%s|%ad" --date=short` to get commits since then
   - For each commit with PR number (format: `#<number>`), extract the PR number
   - Get PR merge dates using `git log --grep="Merge pull request #<number>" --format="%ad" --date=short -1`

2. **Group related changes intelligently**:
   - Look for commits that belong together (e.g., same feature, related fixes)
   - Group by topic/feature when it makes sense
   - Each group becomes one changelog entry
   - For grouped changes, use the **latest PR merge date** as the entry date

3. **Extract commit details**:
   - For commits with PRs, use `git show --stat <commit-hash>` to understand what changed
   - Read commit message bodies for detailed context
   - Convert technical changes into user-facing descriptions

4. **Create changelog entries** following this format:
   ```json
   {
     "id": "YYYY-MM-DD-descriptive-slug",
     "date": "YYYY-MM-DD",
     "title": "User-Facing Title",
     "description": "Clear, concise description of what changed and why users care. 1-2 sentences.",
     "category": "feature|improvement|fix|infra|research",
     "requestedBy": [],
     "pr": 123
   }
   ```

   **For multiple PRs**:
   ```json
   {
     "pr": [123, 456, 789]
   }
   ```

5. **Categorization rules**:
   - `feature`: New functionality users can see/use
   - `improvement`: Enhancements to existing features, UX improvements, performance
   - `fix`: Bug fixes, error handling improvements
   - `infra`: Infrastructure, deployment, CI/CD, developer experience
   - `research`: Experiments, evaluations, research work

6. **User-facing descriptions**:
   - Focus on **what** changed and **why users care**
   - Avoid technical jargon (unless necessary)
   - Be concise but informative (1-2 sentences ideal)
   - Use active voice
   - Examples:
     - ❌ "Refactored admin components to use card pattern"
     - ✅ "Admin console now works beautifully on mobile devices with touch-optimized layouts"
     - ❌ "Added TORALE_NOAUTH_EMAIL environment variable"
     - ✅ "Developers can now configure custom email addresses for no-auth development mode"

7. **Update changelog.json**:
   - Read current `frontend/public/changelog.json`
   - Prepend new entries at the top (reverse chronological order)
   - Maintain exact JSON formatting (2-space indentation)
   - Preserve all existing entries
   - Ensure valid JSON

8. **Handle flags**:
   - If user provides `--rewrite-all`, you can reorganize the entire changelog
   - If user provides `--since <commit>`, use that as starting point instead of last changelog date
   - Default behavior: only add new entries since last changelog update

## Important Notes

- **Always** verify PR numbers exist before including them
- **Always** use PR merge dates, not commit dates (unless no PR)
- **Group intelligently**: Related commits = one entry with multiple PRs
- **Be user-centric**: Users care about features/fixes, not implementation details
- **Maintain quality**: Each entry should be clear, accurate, and valuable
- **No hallucination**: Only include real commits with real PR numbers

## Example Grouping

Given commits:
- `feat: add Python SDK (#28)`
- `fix: SDK error handling (#28)`
- `feat: notification infrastructure (#28)`

These should become **one entry**:
```json
{
  "id": "2025-11-11-python-sdk",
  "date": "2025-11-11",
  "title": "Python SDK with Notification Infrastructure",
  "description": "Beautiful new Python SDK with fluent API for programmatic task management. Create monitors with: monitor().when().notify().create(). Includes comprehensive notification system with email and webhook support.",
  "category": "feature",
  "requestedBy": [],
  "pr": 28
}
```

## Your Task

Update the changelog now. Be thorough, accurate, and user-focused.
