# Contributing

Create branches as `feature/SCRUM-NN-slug` and use commit messages in the
format `SCRUM-NN: imperative message`. The Jira key must be in both the pull
request title and body so work is traceable and automatically linked to the
correct ticket.

Pull requests target `main`, require at least one review, and must pass the
required CI status checks before merge. Branch protection is a GitHub setting
that a repository administrator must apply.

For local backend work:

```powershell
cd backend
py -m pip install -r requirements.txt
py -m pytest tests -q
```
