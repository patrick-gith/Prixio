Prixio (PriceIQ) est une API de comparaison de prix basée sur Django, utilisant des workers Celery, la génération de PDF et des adaptateurs multi-sources (eBay, Google Livres). Le code est relativement modulaire, sans fichiers de configuration, avec une documentation correcte et quelques tests couvrant la logique de tarification et les adaptateurs. Cependant, la couverture de test est superficielle (5 fichiers de spécification pour 89 fichiers sources). L'intégration continue n'exécute jamais de tests ni d'analyse statique (seuls des workflows Celery planifiés existent). Il n'y a pas de fichier de verrouillage et le fichier settings.py contient une clé secrète de secours non sécurisée et un mot de passe de base de données locale codés en dur. Le projet a été classé comme backend principal avec un signal de sécurité secondaire. L'historique Git montre un seul auteur avec une rafale de 29 commits en 4 jours, suggérant un projet parallèle récent et indépendant plutôt qu'un système de production maintenu depuis longtemps.




ation à l'acheteur · ce que mesurent désormais les acheteurs de formations en IA
△
Compilations et tests estimés chez HEAD
Des tests existent (pytest) mais aucun fichier de verrouillage validé, faites fonctionner `install, build, test` à partir d'un clone frais.
✗
Capacité de travail
Quasiment aucun commit exploitable. La valeur est proportionnelle à la capacité des tâches, et la qualité multipliée par zéro tâche est nulle.
△
Histoire authentique
L'histoire écrite par un seul auteur : authentique, certes, mais bien moins riche que les échanges d'une équipe.
△
Autonome
Dockerfile uniquement ; si l’application a besoin de bases de données ou de services associés, ajoutez un fichier docker-compose qui les lance également.
✓
Ceci n'est pas une démo
Rien ne laisse supposer la présence d'une démo ou d'un modèle.
Les critères d'achat évoluent : au-delà du score de qualité, les acheteurs évaluent désormais si un dépôt installe, compile et exécute ses propres tests, s'il peut être utilisé de manière isolée et quelle quantité d'historique de développement exploitable il contient. Ces informations sont extraites des artefacts du dépôt. L'évaluation n'exécute jamais votre code.



Architecture et robustesse
Structure en couches Django (modèles/vues/services/adaptateurs) avec logique de nouvelle tentative et classes de données dans services.py, mais logging_framework:null, aucun suivi des erreurs, aucun point de terminaison de santé/métriques malgré le fait qu'il s'agisse d'un service API
42
B
Couverture des tests
5 fichiers de spécifications de test contre 89 fichiers sources (ratio 1:17), pytest.ini configuré mais aucun seuil de couverture appliqué dans l'intégration continue (ci_runs_tests:false)
28
C
Propreté du code
Aucun fichier principal de plus de 500 lignes de code (le plus volumineux étant settings.py à 276 lignes de code), mais has_lint_config:false et aucun linters_and_formatters configurés
55
F
Documentation et intégration
Le fichier README.md (138 lignes) est un texte marketing en anglais et en français, sans sections d'installation, d'exécution, d'environnement ni d'architecture, et sans fichier .env.example malgré la présence de plus de 20 variables d'environnement référencées dans le code source.
45
je
Hygiène et sécurité
hardcoded_secret_hits:2 incluant LOCAL_SECRET_KEY='django-insecure-local-dev-only-change-this' et un mot de passe de base de données locale codé en dur '1234' dans settings.py, aucun dep_audit_in_ci
35
E
Santé dépendante
Le fichier requirements.txt est présent, mais lockfiles_found est vide et dep_update_tooling est défini sur none, avec plus de 70 dépendances épinglées, mais aucune discipline poetry.lock/uv.lock.
30
H
Maturité CI/CD
L'intégration continue est présente (.github/workflows) mais ci_runs_tests:false, ci_runs_lint:false, ci_runs_typecheck:false ; les workflows ne lancent que des tâches Celery planifiées, et non des contrôles qualité.
25
K
Historique et entretien
git_stats affiche total_commits:29, span_days:4, human_authors:1, tag_count:0, indiquant une très courte période d'activité d'un seul auteur sans cadence de publication.
30
Sécurité · dimensions
50 % du dépôt
29,8 · F
D
Architecture et robustesse
Architecture Django en couches avec des classes de données typées (CollectResult) mais sans framework de journalisation structurée ni de suivi des erreurs configuré.
42
B
Couverture des tests
5 fichiers de test pour 89 fichiers sources (ratio 1:17), pytest configuré mais non appliqué dans l'intégration continue
28
C
Propreté du code
Aucun fichier de plus de 500 lignes de code selon repo_stats, mais has_lint_config:false
55
F
Documentation et intégration
Le fichier README.md contient 138 lignes de contenu purement marketing, sans fichier .env.example malgré la présence de 20 variables d'environnement référencées, dont EBAY_CLIENT_SECRET et TELEGRAM_BOT_TOKEN.
45
je
Hygiène et sécurité
Clé de secours SECRET_KEY non sécurisée codée en dur et mot de passe de base de données locale en clair « 1234 » dans ProjectPrixio/settings.py, aucun modèle de validation des entrées détecté, aucun audit des dépendances dans l'intégration continue
30
E
Santé dépendante
Aucun fichier de verrouillage trouvé malgré un fichier requirements.txt contenant plus de 70 dépendances épinglées, outil de mise à jour des dépendances : aucun
30
H
Maturité CI/CD
L'intégration continue (CI) se limite aux workflows planifiés de Celery (celery-beat.yml, celery-worker.yml) ; aucune tâche de lint/test/vérification de type n'est exécutée sur les demandes de tirage (PR).
25
K
Historique et entretien
git_stats : 29 commits en 4 jours par un seul auteur, tag_count : 0, aucun signal de maintenance continu
30
P
Modélisation des secrets et des menaces
Aucun fichier SECURITY.md, aucune utilisation de secret-manager détectée, les secrets sont transmis uniquement via les variables d'environnement GitHub Actions pour les flux de travail d'intégration continue, aucun modèle de menace documenté n'a été trouvé.





















Comment améliorer ce score
En priorité les correctifs essentiels pour les acheteurs, puis ceux classés par impact prévu.
01
Déployez les fonctionnalités avec leurs tests, dans de petits commits ciblés.
impact sur les paiements
impact élevé
La valeur est proportionnelle à la quantité d'historique exploitable pour créer des tâches d'ingénierie autonomes, c'est-à-dire des modifications validées par des tests. Les commits importants et hétérogènes ainsi que les modifications non testées ne sont pas pris en compte.

Conservez chaque fonctionnalité ou correction dans son propre commit (ou petite PR) qui inclut les tests qui valident le nouveau comportement.
Évitez les commits groupés qui mélangent formatage, refactorisations et nouvelles fonctionnalités ; ils masquent le travail exploitable.
02
Effectuez l'installation, la compilation et les tests à partir d'un clone neuf.
impact sur les paiements
impact élevé
L'un des principaux facteurs influençant le prix payé par les acheteurs est la capacité du projet à se compiler et à exécuter sa suite de tests, dès aujourd'hui, sur une machine qui ne l'a jamais utilisée. Les tests existent, mais le cheminement d'une copie propre à une suite de tests fonctionnelle n'est pas vérifiable. Comblez les lacunes ci-dessous.

Clonez le dépôt dans un répertoire vide et suivez uniquement le fichier README : chaque étape manquante est une étape à ajouter.
Créez un fichier de verrouillage pour chaque gestionnaire de paquets afin que les installations soient reproductibles.
Rendez la commande de test explicite dans le fichier README et le système d'intégration continue (CI), et assurez-vous que le CI l'exécute à chaque envoi de paquets.
03
Continuez à développer ce dépôt au fil du temps, par petites étapes.
impact sur les paiements
impact moyen
Les acheteurs considèrent l'historique des modifications comme une évaluation du produit : un projet développé rapidement ou par une seule personne est moins fiable qu'un projet issu d'un développement continu et collaboratif. Rien de superficiel ne peut y remédier ; seul un travail sérieux et constant le permet.

Continuez à intégrer de véritables changements par petites mises à jour au cours des prochaines semaines ; un historique constant vaut mieux qu’une version peaufinée.
Si des coéquipiers contribuent, demandez-leur de signer sous leur propre identité afin que l'historique montre plus d'un auteur humain.
04
Augmentez la couverture des tests grâce à des spécifications comportementales liées aux fonctionnalités.
impact élevé
B · Couverture des tests
Seuls 5 fichiers de spécifications couvrent 89 fichiers sources (ratio 1:17) et les modules principaux comme PricingApp/views_batch.py ​​(250 LOC) et PrixioApp/views.py (229 LOC) n'ont aucun test visible.

Ajoutez PricingApp/tests/test_views_batch.py ​​couvrant les chemins de succès batch_new, batch_verify et d'erreur de validation en utilisant les fixtures pytest-django et factory_boy déjà présentes dans requirements.txt.
Ajoutez PrixioApp/tests/test_views.py couvrant dashboard, add_to_watchlist, remove_from_watchlist avec @pytest.mark.django_db.
Configurez pytest-cov dans pytest.ini avec --cov=PricingApp --cov=PrixioApp --cov-fail-under=50 et intégrez chaque fichier de test à la fonctionnalité qu'il couvre dans de petits commits.
Exécutez pytest --cov et vérifiez que le pourcentage de couverture global affiché est égal ou supérieur à 50 % sans aucun échec.
05
Rendre un clone frais exécutable sans configuration secrète manuelle
impact élevé
F · Documentation et intégration
Aucun fichier .env.example n'existe malgré la présence de plus de 20 variables d'environnement référencées dans le code source (EBAY_CLIENT_SECRET, DJANGO_SECRET_KEY, RENDER_DATABASE_URL) et le fait que settings.py utilise une clé non sécurisée codée en dur et un mot de passe de base de données en clair « 1234 ».

Créez un fichier .env.example à la racine du dépôt listant toutes les variables de env_vars_referenced_in_source avec des valeurs d'espace réservé, par exemple DJANGO_SECRET_KEY=changeme, EBAY_CLIENT_ID=changeme.
Modifiez le fichier ProjectPrixio/settings.py pour supprimer le mot de passe de secours en clair « 1234 » pour les bases de données et exigez plutôt l’URL de la base de données ou générez une erreur claire.
Ajoutez un fichier docker-compose.yml définissant les services web et postgres afin que `docker compose up` lance l'application et la base de données sans configuration manuelle.
Vérifiez qu'un clone récent peut exécuter `docker compose up` puis `python manage.py test` avec succès et le code de sortie 0.
06
Supprimez les valeurs par défaut codées en dur, assimilables à des secrets, du fichier settings.py.
impact moyen
I · Hygiène et sécurité
repo_stats flags 2 hardcoded_secret_hits: LOCAL_SECRET_KEY dans ProjectPrixio/settings.py ligne 26 et un mot de passe de test dans conftest.py ligne 16.

Modifiez le fichier ProjectPrixio/settings.py pour supprimer la constante LOCAL_SECRET_KEY et générer une exception RuntimeError si DJANGO_SECRET_KEY n'est pas défini en dehors du mode IS_TESTING.
Modifiez la ligne 16 de conftest.py pour récupérer le mot de passe de l'utilisateur de test à partir d'une variable d'environnement ou d'une constante fixe ne ressemblant pas à une information d'identification comme TEST_USER_PW afin d'éviter les faux positifs du scanner de secrets.
Validez les deux modifications simultanément avec un court message décrivant la correction de sécurité, puis exécutez la suite de tests existante pour confirmer l'absence de dysfonctionnement.
07
Ajouter l'analyse statique de code, la vérification des types et l'audit des dépendances à l'intégration continue
impact moyen
H · Maturité CI/CD
ci_runs_lint et ci_runs_typecheck sont tous deux faux et dep_audit_in_ci est faux ; les 4 workflows existants dans .github/workflows sont des tâches cron/deploy, pas un contrôle de qualité des PR.

Créez un fichier .github/workflows/ci.yml déclenché par une pull_request qui exécute ruff check et mypy PricingApp PrixioApp CatalogApp CoreApp en tant qu'étapes séparées.
Ajoutez une étape au même flux de travail, exécutant pip install pip-audit et pip-audit -r requirements.txt pour faire apparaître les paquets épinglés vulnérables.
Ajouter la mise en cache pour pip via actions/setup-python cache : pip comme déjà utilisé dans celery-worker.yml par souci de cohérence.
Confirmez que la nouvelle exécution du flux de travail montre que les tâches de lint, de vérification de type, de test et d'audit réussissent toutes (coches vertes) sur un exemple de PR.
08
Créez un fichier de verrouillage pour des installations reproductibles.
faible impact
E · Santé dépendante
La variable lockfiles_found est vide même si requirements.txt spécifie des versions exactes ; dep_update_tooling est nulle, ce qui risque d’entraîner un décalage entre les dépendances déclarées et résolues.

Exécutez pip-compile ou `pip freeze > requirements.lock.txt` après une installation propre de requirements.txt dans un environnement virtuel et validez requirements.lock.txt.
Ajoutez une configuration Dependabot dans .github/dependabot.yml pour l'écosystème pip avec une planification hebdomadaire pour signaler les versions épinglées obsolètes.
Utilisez le fichier requirements.lock.txt dans l'étape d'installation du flux de travail CI au lieu du fichier requirements.txt directement pour les builds déterministes.