# PriceIQ (Prixio)

> Comparateur de prix multi-sources — API Django + Celery.

## Installation (clone frais)

Prérequis : Python 3.12+, PostgreSQL 16 (ou Docker).

```bash
git clone <repo> && cd Prixio
python -m venv .venv
source .venv/bin/activate          # Windows : .venv\Scripts\activate
pip install -r requirements.lock.txt

cp .env.example .env
# Renseigne au minimum :
#   DJANGO_SECRET_KEY=<genere-en-une>
#   DB_PASSWORD=<mot-de-passe>
#   (ou DATABASE_URL=postgres://user:pass@host:5432/db)

python manage.py migrate
python manage.py runserver



# PriceIQ

**EN** — Paste a product. Get an answer.
**FR** — Collez un produit. Obtenez une réponse.

> Is this price good? Where is it cheapest? Should I buy now?
> Est-ce que ce prix est bon ? Où est-il le moins cher ? Faut-il acheter maintenant ?

---
---

# 🇬🇧 ENGLISH

## The problem nobody solves

Every day, millions of people and businesses ask the same question:

> *"Am I paying the right price?"*

And every day, they answer it blindly.

- **The buyer** opens four tabs, wastes 20 minutes, gives up.
- **The seller** finds out three weeks too late that a competitor was 15% cheaper.
- **The procurement manager** orders at the wrong time and leaves €10,000 on the table.

Nobody has time to do this by hand.
**PriceIQ does it in 3 seconds.**

---

## The promise

**One identifier. One clear answer. Zero effort.**

You paste an ISBN, a barcode, a product name, or a URL.
PriceIQ queries the world, analyzes the history, and tells you:

🔥 **Buy now** — it's 28% cheaper than usual.
⚠️ **Careful** — you're 9% above market.
📌 **Wait** — the price will drop in 3 weeks.

No unreadable chart. No Excel table. **An answer.**

---

## What it changes, concretely

### 🛍️ For a buyer — "I stop getting ripped off"

**Before:** four tabs, 20 minutes, permanent doubt.
**After:** one pasted identifier, an answer in 3 seconds, a confident purchase.

**Real example:**

> Marie is looking for *The Little Prince*.
> She pastes the ISBN. The app answers:
>
> **🔥 84/100 — Excellent deal**
> Best price: **€8.90** (Amazon DE)
> Usual price: €12.40
> **You save: €3.50**
>
> She buys. She stops second-guessing. She comes back next week.

---

### 📊 For an e-commerce seller — "I stop losing sales"

**Before:** he finds out he's too expensive when his sales collapse.
**After:** he knows in real time whether he's competitive, on every product.

**Real example:**

> Karim sells headphones.
> He enters his product and his price. The app answers:
>
> **⚠️ You're 9.4% above market**
> Global median: €319
> Your price: €349
> **Suggested price: €312**
>
> Seven sellers are cheaper than him. He adjusts in 30 seconds. Sales recover.

---

### 🛒 For a procurement manager — "I stop wasting budget"

**Before:** he orders when the need arises. Not when the price is right.
**After:** he knows exactly when and where to buy.

**Real example:**

> Sophie needs to buy 20 graphics cards for her company.
> She enters the product, the quantity, the deadline. The app answers:
>
> **📌 SIGNAL: WAIT**
> The price will drop ~6% in 3 weeks.
> **Estimated savings: €1,840**
> Best region: 🇩🇪 Germany (€549/unit instead of €641)
>
> She waits. She saves. She tells her boss about the app.

---

## What PriceIQ does — in 4 verbs







# PriceIQ

> **Collez un produit. Obtenez une réponse.**
> Est-ce que ce prix est bon ? Où est-il le moins cher ? Faut-il acheter maintenant ?

---

## Le problème que personne ne résout

Chaque jour, des millions de personnes et d'entreprises se posent la même question :

> *« Est-ce que je paie le bon prix ? »*

Et chaque jour, elles répondent à l'aveugle.

- **L'acheteur** compare 4 onglets ouverts, perd 20 minutes, et abandonne.
- **Le vendeur** découvre 3 semaines trop tard qu'un concurrent vendait 15% moins cher.
- **L'acheteur pro** commande au mauvais moment et laisse 10 000 € sur la table.

Personne n'a le temps de faire ça à la main.
**PriceIQ le fait en 3 secondes.**

---

## La promesse

**Un identifiant. Une réponse claire. Zéro effort.**

Vous collez un ISBN, un code-barres, un nom de produit ou une URL.
PriceIQ interroge le monde entier, analyse l'historique, et vous dit :

🔥 **Achète maintenant** — c'est 28% moins cher que d'habitude.
⚠️ **Attention** — tu es 9% plus cher que le marché.
📌 **Attends** — le prix va baisser dans 3 semaines.

Pas de graphique illisible. Pas de tableau Excel. **Une réponse.**

---

## Ce que ça change, concrètement

### 🛍️ Pour un acheteur — « Je ne me fais plus avoir »

**Avant :** 4 onglets, 20 minutes, doute permanent.
**Après :** un identifiant collé, une réponse en 3 secondes, achat serein.

**Exemple réel :**

> Marie cherche *Le Petit Prince*.
> Elle colle l'ISBN. L'app répond :
>
> **🔥 84/100 — Excellente affaire**
> Meilleur prix : **8,90 €** (Amazon DE)
> Prix habituel : 12,40 €
> **Économie : 3,50 €**
>
> Elle achète. Elle ne réfléchit plus. Elle revient la semaine suivante.

---

### 📊 Pour un e-commerçant — « J'arrête de perdre des ventes »

**Avant :** il découvre qu'il est trop cher quand ses ventes chutent.
**Après :** il sait en temps réel s'il est compétitif, sur chaque produit.

**Exemple réel :**

> Karim vend des casques audio.
> Il entre son produit + son prix. L'app répond :
>
> **⚠️ Tu es 9,4% plus cher que le marché**
> Médiane mondiale : 319 €
> Ton prix : 349 €
> **Prix suggéré : 312 €**
>
> 7 vendeurs sont moins chers que lui. Il ajuste en 30 secondes. Ses ventes reprennent.

---

### 🛒 Pour un acheteur pro — « J'arrête de gaspiller du budget »

**Avant :** il commande quand le besoin arrive. Pas quand le prix est bon.
**Après :** il sait exactement quand et où acheter.

**Exemple réel :**

> Sophie doit acheter 20 cartes graphiques pour sa PME.
> Elle entre le produit, la quantité, la deadline. L'app répond :
>
> **📌 SIGNAL : ATTENDS**
> Le prix va baisser de ~6% dans 3 semaines.
> **Économie estimée : 1 840 €**
> Meilleure région : 🇩🇪 Allemagne (549 €/u au lieu de 641 €)
>
> Elle attend. Elle économise. Elle recommande l'app à son patron.

---

## Ce que PriceIQ fait — en 4 verbes


