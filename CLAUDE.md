# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

This is the `.github` organisation-level repository for **keleo-labs**. On GitHub, `.github` repositories serve a special role: they host the organisation profile README (displayed on the org's GitHub page), default community health files (issue templates, contributing guidelines, code of conduct), and reusable workflow templates.

`profile/README.md` is the public-facing description of the Keleo project as a whole, rendered on the organisation's GitHub page. The root `README.md` describes this repository itself.

## The Keleo Project

Keleo is an open, composable framework for describing working practices and methods across any domain. It draws on SEMAT Essence to separate the universal *what* (a kernel of things always present in any endeavour) from the variable *how* (practices that teams choose and compose). The framework has four layers: Language (schema), Baseline (common kernel), Practices (specific guidance), and Methods (composed stacks).

## Sibling Repositories

All sibling repos live under `../` relative to this repository (the local directory is named `dot.github`):

| Local directory | GitHub repo | Role |
|---|---|---|
| `keleo-language` | keleo-labs/keleo-language | JSON Schema (Draft 2020-12) defining the Practice Language meta-model. Canonical source consumed by other projects via symlinks. |
| `keleo-studio` | keleo-labs/keleo-studio | Next.js application for authoring, validating, visualising, and composing practices. |
| `keleo-pgen-llm` | keleo-labs/keleo-pgen-llm | LLM-powered pipeline converting methodology documentation into schema-compliant JSON. |
| `keleo-platforms` | keleo-labs/keleo-platforms | Practice and method content for infrastructure platform engineering. |
| `keleo-horticulture` | keleo-labs/keleo-horticulture | Practice and method content for professional horticulture (domain-agnosticism proof). |
| `keleo-horticulture-docs` | keleo-labs/keleo-horticulture-docs | Source documentation for the horticulture domain, input to the generation pipeline. |
| `keleo-template` | keleo-labs/keleo-template | Template repository for creating new practice/method content repos. |

## Working in This Repo

This repo contains no build system, tests, or application code. Changes are typically limited to:

- Editing `profile/README.md` (the organisation profile)
- Adding or updating community health files (e.g., `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, issue/PR templates under `.github/`)
- Adding reusable GitHub Actions workflow templates

When editing the profile README, preserve the existing structure: problem statement, insight, approach (with the four-layer table), repository index, and getting started guide. The profile README serves as the entry point for anyone discovering Keleo, so clarity and accuracy of the repo descriptions matter.

## Cross-Repo Context

The parent directory (`../`) has a shared `.claude/settings.local.json` with permissions for operations that span repos (symlink creation between keleo-language and consuming projects, `gh api` calls). When making changes here that affect how other repos are described or linked, check that the sibling repo READMEs and this org-level README stay consistent.
