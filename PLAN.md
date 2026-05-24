# semantic-git-diff — PLAN.md

> `git diff` te dit *quoi* a changé. Ce tool te dit *ce que ça signifie.*

---

## Problème

Un diff ligne par ligne est illisible pour quiconque ne connaît pas le codebase en détail.
Les code reviews traînent, les changelogs se font à la main, et personne ne comprend
l'intent d'un commit sans lire chaque fichier.

---

## Objectif

Générer automatiquement un résumé sémantique de n'importe quel diff git en sortie markdown propre,
sans intervention humaine.

Usage : `sgd main..feature/auth`

---

## Scope v1

**In scope**
- Parsing du diff git entre deux refs (commits, branches, tags)
- Chunking par fonction / classe / module
- Envoi des chunks à un LLM local avec prompt structuré
- Synthèse globale en un seul prompt (pas de résumé de résumés)
- Sortie markdown avec résumé global + détail par fichier
- CLI : `sgd <ref1>..<ref2> [--output FILE] [--model MODEL] [--lang LANG] [--dry-run]`

**Out of scope (v1)**
- Interface web / dashboard
- Diffs de plus de 50 fichiers
- Détection de bugs ou suggestions de refactoring
- Git hook (future work)
- GitHub Action (future work)

---

## Architecture

```
git diff (raw)
    │
    ▼
unidiff parser          → PatchSet → PatchedFile → Hunk
    │
    ▼
Chunker sémantique      → regex sur def/class/fn/func/public/async function
    │                      fallback : hunk entier si boundary non détecté
    ▼
Prompt builder          → old_code + new_code comme blocs séparés (pas de +/-)
    │
    ▼
LLM (Ollama / vLLM)    → Qwen3-8B local, un seul prompt de synthèse globale
    │
    ▼
Formatter               → Markdown (défaut) | JSON (--format json)
    │
    ▼
Output                  → stdout ou --output FILE
```

---

## Décisions de design

### 1. Langue de l'output
**English par défaut**, flag `--lang` optionnel.
- Meilleure qualité sur Qwen3 (entraîné majoritairement en anglais sur du code)
- La plupart des codebases ont déjà leurs comments en anglais
- `--lang fr` disponible mais polish post-v1

### 2. Format des chunks envoyés au LLM
**Strip des préfixes `+`/`-`** avant envoi.
- Le prompt passe `old_code` et `new_code` comme deux blocs séparés
- Plus propre, meilleure compréhension de la transformation par le modèle
- Les préfixes restent visibles dans `--dry-run` pour le debug humain

### 3. Flag `--dry-run`
**Oui, dès v1** — pas du polish.
- Affiche : chunks détectés, prompt exact, token count estimé
- Aucun appel LLM
- Indispensable pour valider le chunker avant de bruler des tokens

---

## Prompt template

```
You are an expert code reviewer.

[CONTEXT]
File: {filepath}
Function: {function_name}

[BEFORE]
{old_code}

[AFTER]
{new_code}

Describe in one sentence what changed functionally. No unnecessary technical jargon.
```

Synthèse globale : tous les chunks en un seul prompt, pas de résumé de résumés.
Garde-fou : `if total_tokens > 24000: warn + truncate`, flag `--max-chunks=N`.

---

## Stack

| Composant     | Choix              | Pourquoi                              |
|---------------|--------------------|---------------------------------------|
| Parsing       | `unidiff`          | Mature, gère PatchSet proprement      |
| LLM backend   | `ollama` Python SDK| Zero config, compatible vLLM          |
| CLI           | `typer`            | `--help` propre, type hints natifs    |
| Output        | `rich` + Jinja2    | Rendu terminal + templates markdown   |
| Modèle        | Qwen3-27B dense    | Seuil fiable pour tool use + reasoning|

---

## Jalons weekend

| Bloc          | Durée | Livrable                                      |
|---------------|-------|-----------------------------------------------|
| Samedi matin  | 3h    | Parser + chunker, test sur un vrai diff GitHub |
| Samedi aprem  | 3h    | Intégration LLM, prompt tuning, output markdown|
| Dimanche matin| 2h    | CLI `typer`, `--dry-run`, `--output`, `--lang` |
| Dimanche aprem| 2h    | README avec exemple de sortie, push GitHub     |

---

## Critère de succès

Sur un commit réel (AXIOM-Ω ou qwen-detune), l'output généré doit être compréhensible
par quelqu'un qui ne connaît pas le projet — sans lire une seule ligne de diff.
