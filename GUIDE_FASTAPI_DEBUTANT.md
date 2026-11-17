# Guide pratique : construire une API FastAPI

## Objectif

Ce guide accompagne un débutant, de la définition du besoin jusqu'au déploiement
d'une API. Il prend comme exemple une API de livres avec utilisateurs et avis,
comme dans ce projet. L'objectif est de comprendre l'ordre des étapes, le rôle de
chaque technologie et une organisation qui reste lisible quand l'application grandit.

## 1. Comprendre les composants

| Technologie | Rôle |
| --- | --- |
| **Python** | Langage de l'application et de sa logique métier. |
| **FastAPI** | Déclare les routes HTTP, valide les entrées et produit la documentation OpenAPI. |
| **Starlette / ASGI** | Couche web asynchrone utilisée par FastAPI pour les requêtes et middlewares. |
| **Pydantic** | Valide et transforme les données reçues et renvoyées par l'API. |
| **Uvicorn** | Serveur ASGI qui exécute l'application FastAPI. |
| **SQLAlchemy / SQLModel** | Communiquent avec la base de données; SQLModel combine ORM et modèles typés. |
| **PostgreSQL** | Stocke durablement les utilisateurs, livres, avis et autres données relationnelles. |
| **Alembic** | Versionne et applique les changements de schéma de la base de données. |
| **JWT** | Transporte l'identité et les autorisations dans un jeton signé. |
| **Redis** | Peut servir de cache, de stockage temporaire ou de broker de tâches. |
| **Celery** | Exécute des tâches longues dans un processus worker séparé de l'API. |
| **pytest / HTTPX** | Testent les fonctions et les endpoints sans démarrer un serveur public. |
| **uv** | Gère l'environnement Python, les dépendances et le fichier de verrouillage. |

Une requête suit généralement ce chemin :

```text
Client HTTP
  -> route FastAPI
  -> dépendances (authentification, session, permissions)
  -> service (règles métier)
  -> dépôt / ORM
  -> base de données
  -> schéma de réponse
  -> Client HTTP
```

Le routeur ne devrait pas contenir toute la logique de l'application. Chaque
couche a une responsabilité précise.

## 2. Définir le besoin avant le code

Commencer par répondre à ces questions :

1. Quelles ressources l'API gère-t-elle ? Exemple : utilisateurs, livres, avis.
2. Qui peut faire chaque action ? Exemple : un utilisateur modifie ses propres
   livres; un administrateur consulte toutes les ressources.
3. Quelles données sont obligatoires, uniques ou facultatives ?
4. Quelles erreurs doivent être renvoyées : ressource absente, accès interdit,
   données invalides, conflit ?
5. Quels endpoints sont nécessaires ?

Exemple de contrat :

| Méthode | URL | Usage | Réponse habituelle |
| --- | --- | --- | --- |
| `POST` | `/api/v1/books` | Créer un livre | `201 Created` |
| `GET` | `/api/v1/books` | Lister les livres autorisés | `200 OK` |
| `GET` | `/api/v1/books/{book_id}` | Lire un livre | `200 OK` ou `404` |
| `PATCH` | `/api/v1/books/{book_id}` | Modifier un livre | `200 OK` |
| `DELETE` | `/api/v1/books/{book_id}` | Supprimer un livre | `204 No Content` |

La documentation de ces décisions évite de changer le comportement de l'API au
hasard pendant le développement.

## 3. Créer le projet et gérer les dépendances

Installer une version de Python supportée par les bibliothèques et l'environnement
de déploiement. Initialiser le projet avec `uv` :

```powershell
uv init --package book-api
uv add "fastapi[standard]" pydantic-settings
uv add "sqlalchemy[asyncio]" sqlmodel asyncpg alembic
uv add --dev pytest httpx ruff
```

Ajouter ensuite les dépendances au fur et à mesure des besoins : par exemple
`pyjwt` et `passlib` pour une authentification par jeton, ou `celery[redis]` pour
des tâches d'arrière-plan.

`pyproject.toml` décrit les dépendances directes. `uv.lock` fixe les versions
résolues afin que les environnements de développement, de test et de déploiement
utilisent le même ensemble de paquets. Ne modifiez pas le lockfile à la main.

Créer un `.gitignore` et exclure au minimum `.venv/`, `__pycache__/`, `.env` et les
fichiers temporaires. Committer un `.env.example` sans secrets, jamais le vrai
`.env`.

## 4. Créer l'application minimale

Créer un point d'entrée explicite, par exemple `src/main.py` :

```python
from fastapi import FastAPI

app = FastAPI(title="Book API", version="1.0.0")


@app.get("/health")
async def health_check():
    return {"status": "ok"}
```

Lancer le serveur de développement :

```powershell
uv run uvicorn src.main:app --reload
```

Ouvrir ensuite `http://127.0.0.1:8000/docs` pour essayer l'API et
`http://127.0.0.1:8000/redoc` pour consulter une autre présentation de la
documentation.

## 5. Centraliser la configuration

Les paramètres ne doivent pas être dispersés dans les routes : URL de base de
données, secrets JWT, Redis, SMTP, etc. Les lire depuis des variables
d'environnement avec `pydantic-settings`.

Exemple de `.env.example` :

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/book_api
JWT_SECRET=replace-with-a-random-secret
JWT_ALGORITHM=HS256
REDIS_URL=redis://localhost:6379/0
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM=no-reply@example.com
```

Générer le secret JWT séparément, ne pas réutiliser un mot de passe utilisateur.
Vérifier que les valeurs correspondent aux types et valeurs acceptés par la
configuration : par exemple, si le code autorise uniquement `HS256`, la valeur
`JWT_ALGORITHM` doit être exactement `HS256`.

En production, fournir les secrets via le gestionnaire de secrets de la plateforme
ou ses variables d'environnement, plutôt que par un fichier commité.

## 6. Définir les schémas d'entrée et de sortie

Les schémas Pydantic définissent le contrat HTTP. Séparer les données d'entrée
des données de sortie permet de ne pas exposer des champs internes, comme un hash
de mot de passe.

```python
from pydantic import BaseModel, Field


class BookCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    author: str = Field(min_length=1, max_length=120)


class BookRead(BookCreate):
    uid: str
```

Utiliser des contraintes adaptées au domaine, valider les formats (courriel, UUID,
etc.) et documenter les champs. La validation des données entrantes ne remplace
pas les règles métier : par exemple, vérifier qu'un utilisateur est propriétaire
du livre reste la responsabilité du service.

## 7. Modéliser les données et connecter PostgreSQL

Créer les modèles persistés, leurs clés primaires, contraintes et relations.
Séparer les modèles de base de données des schémas d'API lorsque leur rôle ou
leur évolution diffère.

Créer ensuite une fabrique de sessions SQLAlchemy asynchrones et fournir la
session par une dépendance FastAPI (`Depends`). Une session par requête évite de
partager une transaction entre plusieurs utilisateurs.

Ne pas ouvrir de connexion à la base au moment de l'import d'un module. Créer les
ressources au démarrage de l'application et les fermer proprement à l'arrêt.
Garder une seule définition de chaque table : deux classes ORM distinctes portant
le même nom de table provoquent des conflits de métadonnées.

## 8. Versionner le schéma avec Alembic

Une migration décrit une modification de la base dans le temps. Le cycle habituel :

1. Modifier un modèle.
2. Générer une migration candidate avec `alembic revision --autogenerate`.
3. Lire et corriger le fichier généré : l'autogénération n'est pas infaillible.
4. Appliquer la migration en développement avec `alembic upgrade head`.
5. Tester la migration sur une base de test et l'inclure dans le déploiement.

Les tables de tous les modèles doivent être importées dans la métadonnée utilisée
par Alembic. Pour les environnements de production, privilégier les migrations
explicites plutôt que `metadata.create_all()` au démarrage de l'API.

## 9. Écrire les services et les routes CRUD

Une route devrait surtout :

1. lire les paramètres et le corps de la requête ;
2. déclarer les dépendances ;
3. appeler un service ;
4. choisir le code HTTP et le schéma de réponse.

Le service applique les règles métier et coordonne les opérations. Un dépôt
(`repository`) peut encapsuler les requêtes SQL lorsque celles-ci deviennent
complexes ou répétées; il n'est pas nécessaire d'ajouter cette abstraction à une
petite API qui n'en a pas besoin.

Définir explicitement les `response_model`, les codes de statut et les filtres
d'accès. Pour les listes, prévoir pagination et limites plutôt que renvoyer toutes
les lignes de la base.

## 10. Ajouter authentification et autorisation

Une authentification par jeton suit généralement ce parcours :

1. Créer le compte et hacher le mot de passe avec une fonction de hachage adaptée.
2. À la connexion, vérifier le mot de passe sans jamais le stocker en clair.
3. Émettre un jeton d'accès signé, de durée limitée.
4. Lire le jeton avec une dépendance FastAPI et retrouver l'utilisateur.
5. Vérifier les permissions et la propriété de la ressource avant toute mutation.
6. Gérer révocation et renouvellement si le produit en a besoin.

Authentification et autorisation sont deux choses distinctes : le jeton identifie
l'utilisateur; les contrôles de rôle ou de propriété déterminent ce qu'il peut
faire. Ne jamais renvoyer le hash de mot de passe, les secrets ou les jetons dans
les logs.

## 11. Uniformiser les erreurs et les logs

Créer des exceptions métier explicites (`BookNotFound`, `InsufficientPermission`,
etc.) et les transformer dans un gestionnaire central en réponses cohérentes.
Une erreur de validation peut renvoyer `422`, une ressource absente `404`, et un
accès interdit `403`.

Un middleware est adapté aux préoccupations transversales comme la journalisation
des requêtes ou un identifiant de corrélation. Éviter d'y placer les règles métier.
Journaliser les erreurs inattendues côté serveur sans renvoyer leur trace ou leurs
détails internes au client.

## 12. Déporter les tâches longues avec Celery

L'envoi d'e-mails, la génération de rapports ou le traitement d'images ne devraient
pas bloquer une requête pendant plusieurs secondes. La route valide les données,
place une tâche dans le broker Redis et répond rapidement, souvent avec
`202 Accepted` et un identifiant de tâche.

Le worker Celery consomme la tâche séparément et fait le travail. L'API et le worker
doivent partager la configuration, les modules de tâches et l'accès au broker.
Prévoir reprises limitées, journalisation et tâches idempotentes quand c'est
possible. Ne placer ni mots de passe ni jetons dans les messages de tâche.

En développement Windows, un worker Celery peut être lancé avec le pool `solo` :

```powershell
uv run celery -A src.celery_app:celery_app worker --loglevel=INFO --pool=solo
```

Redis doit être démarré séparément. En production, API, worker et Redis sont des
processus ou services distincts.

## 13. Tester avant de déployer

Écrire des tests à plusieurs niveaux :

- **Unitaires** : services et règles métier, sans réseau ni base réelle.
- **API** : requêtes HTTP avec `TestClient` ou HTTPX, dépendances remplacées par
  des doubles de test.
- **Base de données** : tests d'intégration sur une base isolée et migrations
  appliquées.
- **Tâches** : vérifier que l'API met le bon message en file et que le worker
  traite correctement une tâche; ne pas contacter un vrai SMTP dans les tests.

Tester les cas heureux et les erreurs : données invalides, absence de ressource,
droits insuffisants, indisponibilité du broker, échec de la base. Exécuter les
tests et le linter automatiquement en intégration continue.

Dans ce projet, lancer la suite avec :

```powershell
uv run pytest -q
```

Les tests se trouvent dans `tests/api/`, `tests/unit/` et `tests/tasks/`. Ils
utilisent une configuration isolée et remplacent les accès externes : aucun
PostgreSQL, Redis ou serveur SMTP n'est requis pour cette suite. Les migrations
et les échanges avec de vrais services restent à vérifier séparément dans des
tests d'intégration.

## 14. Déployer l'API

Avant la mise en production :

1. Configurer les secrets, la base, Redis et SMTP dans l'environnement cible.
2. Construire une image ou un paquet reproductible et utiliser des versions de
   dépendances verrouillées.
3. Exécuter les migrations une fois, dans une étape dédiée.
4. Lancer plusieurs processus de serveur ASGI selon les ressources disponibles.
5. Démarrer au moins un worker Celery si des tâches sont utilisées.
6. Configurer HTTPS, limites de requêtes, CORS nécessaire uniquement, health checks
   et sauvegardes.
7. Collecter logs, métriques et erreurs; surveiller les files Celery.

Le mode `--reload` sert au développement, pas à la production.

## Structure recommandée pour un projet important

Pour la plupart des équipes, commencer par un **monolithe modulaire** : une seule
application déployable, organisée par domaines fonctionnels. C'est plus simple à
tester et à exploiter que des microservices, tout en séparant clairement les
responsabilités. N'extraire un service qu'en présence d'un besoin réel de
déploiement, de montée en charge ou d'autonomie d'équipe.

```text
book_api/
├── pyproject.toml
├── uv.lock
├── alembic.ini
├── migrations/
│   ├── env.py
│   └── versions/
├── src/
│   ├── main.py                 # création/configuration de l'application
│   ├── core/
│   │   ├── config.py           # variables d'environnement
│   │   ├── errors.py           # exceptions et handlers globaux
│   │   ├── logging.py
│   │   └── security.py         # helpers JWT et hash
│   ├── db/
│   │   ├── session.py          # engine, sessions et dépendance
│   │   └── base.py             # métadonnées partagées par Alembic
│   ├── modules/
│   │   ├── auth/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── models.py
│   │   │   ├── service.py
│   │   │   ├── repository.py
│   │   │   └── dependencies.py
│   │   ├── books/
│   │   │   ├── router.py
│   │   │   ├── schemas.py
│   │   │   ├── models.py
│   │   │   ├── service.py
│   │   │   └── repository.py
│   │   └── reviews/
│   │       ├── router.py
│   │       ├── schemas.py
│   │       ├── models.py
│   │       ├── service.py
│   │       └── repository.py
│   ├── tasks/
│   │   ├── celery_app.py
│   │   └── email_tasks.py
│   └── middleware/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── api/
├── .env.example
└── .gitignore
```

### Règles d'organisation

- **Organiser par domaine**, pas uniquement par type de fichier à l'échelle de
  toute l'application. Une équipe qui travaille sur `books` doit pouvoir trouver
  ses routes, schémas, service et modèles dans un même module.
- **Garder les routes fines** et les services indépendants de FastAPI autant que
  possible.
- **N'ajouter un repository que lorsqu'il clarifie le code** ou permet de remplacer
  utilement la persistance dans les tests.
- **Éviter les imports circulaires** : utiliser des références typées différées
  pour les relations ORM et centraliser le chargement de la métadonnée pour
  Alembic.
- **Ne pas créer un fichier monolithique `models.py`** pour tous les domaines :
  cela devient difficile à maintenir et favorise les dépendances circulaires.
- **Garder `main.py` comme composition root** : il assemble routers, middleware,
  handlers et cycle de vie, mais ne contient pas les règles métier.
- **Versionner les routes** (par exemple `/api/v1`) et maintenir le contrat public
  compatible lorsque c'est nécessaire.

## Parcours conseillé pour apprendre

Construire d'abord une API CRUD simple sans authentification ni Celery. Ajouter
ensuite la base de données et les migrations, puis les tests, l'authentification,
les permissions, les erreurs centralisées, Redis et enfin Celery. Cette progression
permet de comprendre chaque problème avant d'ajouter une nouvelle technologie.