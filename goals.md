### PROJECT DESCRIPTION

This is a project called ambi alert. The end goal of this project is to do a "reverse search". When something happens on the internet, ping me.

- something happens → My query
- Internet → Going to search
- ping me → Alert me and this could through email

### TASKS

We're not going to build everything in one go. 

You have this file now [called@ambi-backend.py](mailto:called@ambi-backend.py) (also look [at@smolagents-example.py](mailto:at@smolagents-example.py)  for reference). This currently is able to search the web and return a bunch of relevant websites. I want to extend this tool into a bigger project. These are the goals of the project

- User gives a query like "next Iphone" or "geopolitcs in south indian ocean" or "new dominos pizza in the UK"
- Translate the query (or expand it) based on user intent to be a searchable query on duck duck go
- Using existing search functionality, Identify websites to watch.
- Store this in a database of sorts (start with sqlite), but decouple so I can upgrade later
- Implement a monitor to watch the websites everyday (or every N minutes) for changes
- If there is a change, identify whether it is relevant to the query and trigger an alerting system
- Mock an alerting system to send an email.

### REFERENCES

- Smolagents: https://huggingface.co/docs/smolagents/index
- 


### PROJECT STRUCTURE 

This project has been scaffolded using [uv](https://docs.astral.sh/uv/getting-started/installation/), using the following [cookiecutter template](https://github.com/fpgmaas/cookiecutter-uv )

#### IMPORTANT STUFF
- [plan.md](plan.md): This file. This has all your goals
- [progress.md](progress.md): This file. Update progress as you go along

#### GENERAL STUFF
This project uses uv for dependency management.
This project is a python package called ambi-alert.
The package is located in the ambi-alert directory.
There is a foo.py file, which boilerplate code for the package (delete this and the corresponding test).
There is aplan.md file (this file), which is the plan for the project. Cursor AI / Sonnet / GPT use this
README.md is the readme for the package, please update as it goes
Tests are in the tests directory and use pytest
Documentation is in the docs directory and uses mkdocs. Docstrings are Google style.
You're already cd-ed into the ambi-alert directory. This is the directory structure


```
ambi-alert
├── CONTRIBUTING.md
├── Dockerfile
├── docs
│   ├── index.md
│   └── modules.md
├── ambi_alert.egg-info
│   ├── dependency_links.txt
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   └── top_level.txt
├── ambi_alert
│   ├── foo.py
│   ├── __init__.py
├── Makefile
├── mkdocs.yml
├── plan.md
├── pyproject.toml
├── README.md
├── tests
│   └── test_foo.py
├── tox.ini
└── uv.lock
```



### PRINCIPLES

- Build things modularly
- Start lean always
- Keep things "swappable"