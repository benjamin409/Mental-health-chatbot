# Presentation layer — Express + React

The interface people actually use. Express owns the session and the SQLite
database; React renders the pages; classifications come from the Python
inference service over HTTP.

```
  Browser (React)  ──►  Express :3000  ──►  Flask service :5001
                              │
                              └─ SQLite: submissions
```

---

## 1. Install

Requires **Node.js 22.5 or later** (`node --version`).

SQLite comes from Node's own standard library (`node:sqlite`), so there is no
native module to compile and no C++ build tools to install.

```bash
cd web
npm install
```

## 2. Run

The Python service must be running first — Express checks it at start-up and
tells you if it is not there.

```bash
# terminal 1  (project root)
python service/app.py

# terminal 2
cd web
npm run build      # first time, and after any change to client/
npm start          # http://127.0.0.1:3000
```

That is two processes on demonstration day, not three: the React app is built
to static files that Express serves itself.

**While developing the interface**, use the live-reloading setup instead:

```bash
npm run dev        # Express on 3000, Vite on 5173
```

then open **http://localhost:5173** — Vite proxies `/api` to Express, so there
is no CORS configuration to worry about.

## 3. Layout

```
web/
├── server/
│   ├── index.js        Express app, routes, session cookie
│   ├── classifier.js   the only file that talks to the Python service
│   ├── db.js           SQLite, schema per Chapter Three §3.3.6
│   └── config.js       ports, URLs, thresholds
├── client/
│   ├── index.html
│   └── src/
│       ├── App.jsx
│       ├── classes.js          class colours and labels
│       ├── styles.css
│       └── components/
│           ├── EntryForm.jsx
│           ├── Result.jsx
│           ├── Confidence.jsx  the four-way probability bars
│           ├── History.jsx
│           └── About.jsx
├── dist/               built interface (created by npm run build)
└── submissions.db      created on first run
```

## 4. API

| Route | Purpose |
|---|---|
| `POST /api/classify` | `{ text }` → classification; also writes the submission |
| `GET /api/history` | this session's entries, newest first |
| `DELETE /api/history` | delete every entry for this session |
| `DELETE /api/history/:id` | delete one entry |
| `GET /api/health` | is the classifier reachable? |
| `GET /api/info` | deployed model details, for the About page |

## 5. Database

Exactly the schema specified in Chapter Three, §3.3.6:

| Field | Type |
|---|---|
| `submission_id` | INTEGER PRIMARY KEY AUTOINCREMENT |
| `session_token` | TEXT NOT NULL |
| `submitted_text` | TEXT NOT NULL |
| `predicted_class` | TEXT NOT NULL |
| `confidence_score` | REAL NOT NULL |
| `timestamp` | DATETIME NOT NULL |

`submitted_text` stores the entry **as the person wrote it**. An earlier version
stored the cleaned, lemmatised form instead, on the reasoning that keeping less
of what someone wrote is the safer default. The reasoning was sound but the
result was not: the entries page then showed a person their own words back as
`not sleep properly nothing interest me anymore feel empty`, which reads as a
fault in the software and costs more trust than the change bought.

The privacy guarantee does not depend on mangling the text. It rests on there
being no account, no name and no identifier beyond an opaque session token, and
on every entry being deletable by the person who wrote it.

Inspect it with any SQLite viewer, or:

```bash
python -c "import sqlite3;print(*sqlite3.connect('web/submissions.db').execute('select * from submissions'),sep='\n')"
```

## 6. Design decisions to defend

The interface exists to lower the barrier to honest disclosure — the problem
Chapter One identifies as central in a setting where stigma discourages people
from admitting distress. These choices follow from that, and each can be
justified:

- **No account, no name, no email.** A session token in a cookie identifies a
  browser so a person can see their own entries. It identifies no one.
- **The privacy statement appears before the text box**, not in a footer.
  Reassurance after disclosure is too late.
- **The prompt asks how you have been feeling**, not what happened. This
  invites emotional language — which is also, as it happens, what the model
  reads best, so the design requirement and the accuracy requirement agree.
- **Warm paper tones, a serif reading face, and no red anywhere.** It should
  feel like a notebook, not a hospital form. Someone told their writing
  suggests distress does not need an alarm colour.
- **The referral prompt is an invitation.** Same calm treatment as the rest of
  the page.
- **All four probabilities are shown**, not just the winner, so a 51/49 reading
  is visibly different from a confident one.
- **Below 45% confidence the system declines to name a category** and says so
  plainly. A screening aid that presents a guess as a finding misleads the
  person it is meant to help.
- **Every entry can be deleted, individually or all at once.** A record you
  cannot remove is a reason not to write in the first place.
- **No clinical vocabulary in the result.** The wording is always about what
  the words resemble.

## 7. Troubleshooting

**"Classifier NOT REACHABLE" at start-up** — the Python service is not running.
Start it with `python service/app.py` from the project root, then reload.

**`gyp ERR! find VS` / "Could not find any Visual Studio installation"** —
you are on an older copy of this project that used `better-sqlite3`, a native
module with no prebuilt binary for newer Node versions. The current version
uses Node's built-in `node:sqlite` instead and has no native dependency. Delete
`node_modules` and `package-lock.json`, make sure `package.json` no longer
lists `better-sqlite3`, and run `npm install` again.

**`Cannot find module 'node:sqlite'`** — your Node is older than 22.5. Upgrade
to Node 22 LTS or newer.

**Port 3000 already in use** — `PORT=3001 npm start`.

**The classifier is on a different port** — `CLASSIFIER_URL=http://127.0.0.1:8000 npm start`.
