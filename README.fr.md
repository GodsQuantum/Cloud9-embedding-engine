<p align="center">
  <img src="docs/assets/logo.svg" width="132" alt="Logo Cloud9 Embedding Engine">
</p>

<h1 align="center">Cloud9 Embedding Engine</h1>

<p align="center"><strong>Embeddings RDNA-first, API OpenAI-compatible. Benchmark d'abord, index ensuite.</strong></p>

<p align="center">
  <a href="README.md">English</a> · <a href="README.fr.md">Français</a> · <a href="README.zh-CN.md">简体中文</a>
</p>

Cloud9 Embedding Engine est un moteur dédié aux embeddings locaux. Il sert des modèles d'embedding via llama.cpp et une API compatible OpenAI, avec un profil de production conçu pour cohabiter avec un gros LLM sur une Radeon 780M.

## Principes

- un modèle d'embedding petit et séparé du moteur de génération ;
- Vulkan/RDNA validé sur Ryzen 7 8845HS / Radeon 780M ;
- modèle et dimension explicitement verrouillés par index ;
- benchmark avant promotion, avec **contrôle strict des indices de réponse et des vecteurs** (NaN, valeurs nulles, dimensions) pour éviter les faux scores de rappel ; voir [la validation bilingue](docs/model-gate-integrity.md) ;
- profil `production` à 1 slot, `bulk` à 8 slots uniquement pour une ingestion initiale ;
- cache hôte llama.cpp désactivé par défaut (`C9EE_CACHE_RAM=0`) pour éviter plusieurs Gio de RAM inutiles sur des prompts d'embedding uniques ;
- priorité CPU/I/O basse afin que le moteur cède devant les services critiques ;
- aucun changement silencieux de modèle sur un index déjà vectorisé.

## Modèles retenus

| Modèle | Usage | Licence | Contexte | Dimension |
|---|---|---|---:|---:|
| Qwen3-Embedding-0.6B | défaut validé Cloud9 | Apache-2.0 | 32K | 1024 |
| Jina Embeddings v5 Text Small Retrieval | qualité multilingue | CC BY-NC 4.0 | 32K | 1024, Matryoshka |
| IBM Granite Embedding 311M Multilingual R2 | compact / commercial / FR+EN | Apache-2.0 | 32K | 768, Matryoshka |

Jina est volontairement **non activé par défaut** dans un contexte commercial à cause de sa licence.

## Résultat de référence Cloud9

Qwen3-Embedding-0.6B Q8_0 via llama.cpp Vulkan : ~54,9 req/s sur le micro-benchmark séquentiel, ~73,4 embeddings/s à batch 32, et cosinus 0,99959–0,99976 face à la référence TEI/ONNX.

Les gros chunks réels sont plus lents : le moteur inclut donc des profils distincts pour requêtes normales et ingestion massive.

## Démarrage

```bash
./scripts/install.sh
cloud9-embedding-engine doctor
cloud9-embedding-server
```

Voir [docs/models.md](docs/models.md) et [docs/architecture.md](docs/architecture.md).
