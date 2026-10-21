# Setup guide — Windows + VS Code

Getting the system running on your own machine, from nothing to a working
classifier and a live API, with a check at every stage so you always know
whether the last step worked.

Budget about 30 minutes the first time. Nothing here needs to be repeated once
it is done.

**What you will have at the end**

- A working Python environment isolated from the rest of your PC
- The trained model classifying text you type
- The inference API running on `http://127.0.0.1:5001`, ready for your Express
  frontend to call

---

## Step 1 — Install Python

Skip to Step 2 if you already have Python 3.11 or 3.12.

1. Go to <https://www.python.org/downloads/windows/> and download **Python
   3.12** (64-bit installer).

   Do **not** install from the Microsoft Store. The Store version puts files in
   an unusual location and virtual environments behave oddly.

2. Run the installer. On the very first screen, tick:

   > **☑ Add python.exe to PATH**

   This checkbox is at the bottom and is easy to miss. If you skip it, every
   command in this guide fails with `'python' is not recognized`. Then click
   **Install Now**.

3. Close any Command Prompt or PowerShell window that was already open —
   they will not see the new PATH.

**Check it worked.** Open a new PowerShell window (press `Win`, type
`powershell`, Enter) and run:

```powershell
python --version
```

Expected: `Python 3.12.x`. If you get `'python' is not recognized`, see
Troubleshooting A.

---

## Step 2 — Install VS Code and the Python extension

1. Install VS Code from <https://code.visualstudio.com/>.
2. Open it, click the **Extensions** icon in the left bar (or `Ctrl+Shift+X`).
3. Search for **Python** and install the one published by Microsoft.

---

## Step 3 — Unzip the project

Extract `mhms_model.zip` to a simple path such as:

```
C:\projects\mhms
```

Two things to avoid, both of which cause real problems on Windows:

- **Do not put it inside OneDrive** (which usually includes your Desktop and
  Documents folders). OneDrive syncs files while Python is writing them, which
  produces permission errors that look like bugs in the code.
- **Avoid spaces and very long paths.** `C:\projects\mhms` is ideal.

Open the folder in VS Code: **File → Open Folder →** select `mhms`.

You should see `src`, `service`, `models`, `data`, `results` and
`requirements.txt` in the sidebar. If instead you see a single folder called
`mhms` containing those, you opened one level too high — open the inner folder.

---

## Step 4 — Open a terminal inside VS Code

Press ``Ctrl+` `` (the key above Tab). A terminal opens at the bottom, already
in your project folder.

Confirm you are in the right place:

```powershell
dir
```

You should see `requirements.txt`, `src`, `service` and `models` listed. Every
command in this guide is run from this folder — not from inside `src`.

---

## Step 5 — Create the virtual environment

A virtual environment keeps this project's packages separate from everything
else on your PC, so nothing you install here can break another project.

```powershell
python -m venv venv
```

This takes a few seconds and creates a `venv` folder. Now activate it:

```powershell
.\venv\Scripts\Activate.ps1
```

**Check it worked.** Your prompt should now begin with `(venv)`:

```
(venv) PS C:\projects\mhms>
```

If you instead get a red error saying *"running scripts is disabled on this
system"*, that is normal on a fresh Windows install — see Troubleshooting B.
It takes one command to fix.

> **Every time you open a new terminal you must activate the environment
> again.** If a command fails with `ModuleNotFoundError`, the missing `(venv)`
> in your prompt is almost always the reason.

---

## Step 6 — Install the packages

```powershell
pip install -r requirements.txt
```

This downloads roughly 150 MB and takes 3–10 minutes depending on your
connection. Warnings in yellow are fine. Red `ERROR` lines are not — see
Troubleshooting D.

**Check it worked.**

```powershell
python -c "import sklearn, nltk, flask, pandas; print('all packages OK')"
```

Expected output: `all packages OK`

---

## Step 7 — Point VS Code at the environment

VS Code needs to be told to use the environment you just made, otherwise its
error-underlining will be wrong even though your terminal commands work.

1. Press `Ctrl+Shift+P`
2. Type `Python: Select Interpreter` and press Enter
3. Choose the one showing `.\venv\Scripts\python.exe` — it is usually marked
   **Recommended**

---

## Step 8 — Check the model works

The trained model ships with the project, so there is nothing to train before
this works.

```powershell
python src\predict.py "I have not been sleeping properly and nothing interests me anymore"
```

Expected output:

```
Model in use: Logistic Regression
----------------------------------------------------------------------
INPUT      : I have not been sleeping properly and nothing interests me anymore
CLEANED    : not sleep properly nothing interest me anymore
PREDICTION : Depression (confidence 9X.XX%)
DISTRIBUTION: Depression XX.X%, Normal X.X%, Anxiety X.X%, Stress X.X%
HEADLINE   : Language consistent with depressive expression
REFERRAL   : Consider speaking with someone you trust ...
----------------------------------------------------------------------
```

The exact percentages will match what is reported in Chapter Four.

Try it interactively too — run `python src\predict.py` with no text, type
sentences, and press Enter on an empty line to quit.

**If you get `InconsistentVersionWarning` or an unpickling error**, your
scikit-learn version differs from the one the model was saved with. See
Troubleshooting E — the fix is to retrain, and it is straightforward.

---

## Step 9 — Run the verification suite

```powershell
python src\test_system.py
```

Expected ending:

```
RESULT: all functional tests passed.
        2 sanity case(s) did not match the expected class (informational only).
```

The two sanity misses are expected and documented — they are the known weakness
of the Stress class, discussed in Chapter Four. **"all functional tests
passed" is the line that matters.**

At this point the machine-learning half of your project is working on your PC.

---

## Step 10 — Start the inference service

```powershell
python service\app.py
```

Expected output:

```
09:12:04  INFO     Model loaded: Logistic Regression (0.07s)
09:12:04  INFO     Classes: Anxiety, Depression, Normal, Stress
09:12:04  INFO     Listening on http://127.0.0.1:5001
 * Running on http://127.0.0.1:5001
```

The line *"WARNING: This is a development server"* is normal and can be
ignored — it is Flask reminding you this is not a production deployment, which
is exactly right for a project demonstration.

**Windows Firewall may show a prompt** the first time. Tick **Private
networks** and allow it. If you dismiss it by accident, nothing breaks — the
service only listens on `127.0.0.1`, which is your own machine.

**This terminal is now busy.** The service runs until you press `Ctrl+C`. Leave
it running and open a second terminal for the next step.

---

## Step 11 — Test the API from a second terminal

In VS Code, click the **`+`** icon at the top-right of the terminal panel to
open a second terminal (or the split-pane icon beside it to see both at once).

Activate the environment in this new terminal too:

```powershell
.\venv\Scripts\Activate.ps1
python service\test_api.py
```

Expected ending:

```
RESULT: 40 passed, 0 failed
```

That is the whole backend verified: every endpoint, every error path, and the
response shape your Express code will depend on.

### Trying a single request by hand

**Do not use `curl` in PowerShell.** PowerShell aliases `curl` to a different
command with different syntax, and you will get a confusing error. Use this
instead:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5001/classify -Method Post `
  -ContentType "application/json" `
  -Body '{"text":"I keep worrying about everything and my heart races"}'
```

You can also just open <http://127.0.0.1:5001/info> in your browser to see the
deployed model's details.

---

## Step 12 — Retraining (optional)

You do **not** need to do this — the trained model is included, and the figures
in `results/` were produced from it. Do it only if you change the
pre-processing, change the model settings, or hit the version problem in
Troubleshooting E.

```powershell
python src\prepare_data.py          # about 40 seconds
python src\train.py --no-cv         # about 8 minutes
python src\evaluate.py              # about 15 seconds
```

Without `--no-cv` the full run including 5-fold cross-validation takes 30–40
minutes, most of it the Random Forest. Use the full version when you want the
cross-validation column in Table 4.1 regenerated; `--no-cv` is fine otherwise.

Everything is seeded with `random_state = 42`, so you will get the same numbers
that are in Chapter Four.

---

## Your daily routine, once set up

Open VS Code on the project folder, then:

```powershell
.\venv\Scripts\Activate.ps1     # terminal 1
python service\app.py           # leave running
```

```powershell
.\venv\Scripts\Activate.ps1     # terminal 2
npm start                       # your Express app, once you build it
```

Service first, then Express. Your Node app should call `GET /health` when it
starts so it can tell you immediately if the classifier is not up.

---

## Troubleshooting

### A. `'python' is not recognized as an internal or external command`

Python is not on your PATH. Three options, easiest first:

1. Try `py` instead of `python` — the Windows launcher is often present even
   when `python` is not: `py --version`, `py -m venv venv`.
2. Re-run the Python installer, choose **Modify**, click Next, and tick
   **Add Python to environment variables**.
3. Close and reopen your terminal — a terminal opened before installation
   still holds the old PATH.

### B. `Activate.ps1 cannot be loaded because running scripts is disabled`

Windows blocks PowerShell scripts by default. Run this once:

```powershell
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned
```

Answer `Y`. Then run `.\venv\Scripts\Activate.ps1` again. This applies to your
user account only and is the setting Microsoft recommends for developers.

Alternatively, switch the VS Code terminal to Command Prompt (click the `∨`
beside the `+` icon → **Command Prompt**) and use `venv\Scripts\activate.bat`.

### C. `ModuleNotFoundError: No module named 'sklearn'` (or nltk, flask, ...)

Your prompt is missing `(venv)`. Activate the environment:

```powershell
.\venv\Scripts\Activate.ps1
```

If the prompt does show `(venv)` and it still fails, the packages did not
install — repeat Step 6 and read the output for red `ERROR` lines.

### D. `pip` fails, or `'pip' is not recognized`

Use pip through Python instead, which always works:

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

If a package fails to build rather than download, your Python version is
probably too new for a pre-built wheel. Install Python 3.12 and rebuild the
environment: delete the `venv` folder and repeat Step 5.

### E. `InconsistentVersionWarning`, or the model will not load

The model was serialised with scikit-learn 1.8.0. If pip installed a different
version, retrain to regenerate the files for your version:

```powershell
python src\prepare_data.py
python src\train.py --no-cv
```

About 9 minutes total. Everything downstream then works normally.

### F. `Trained artefacts not found` / `ModuleNotFoundError: No module named 'config'`

You are running from the wrong folder. All commands run from the project root
(`C:\projects\mhms`), not from inside `src`. Check with `dir` — you should see
`requirements.txt` in the listing. If you are inside `src`, run `cd ..`.

### G. `Address already in use`, or port 5001 is taken

Either the service is already running in another terminal, or another program
has the port. Run it on a different port:

```powershell
$env:PORT="5002"
python service\app.py
```

Remember to point your Express app at the new port.

### H. The service starts but requests hang or fail

- Confirm it is actually running — look for `Listening on http://127.0.0.1:5001`
  in the first terminal.
- Confirm you are calling `127.0.0.1`, not `localhost` — on some Windows
  configurations `localhost` resolves to IPv6 first and the connection is
  refused.
- Check the service terminal: every request is logged there with its status
  code, so you can see whether it arrived at all.

### I. Everything is very slow, or antivirus interferes

Some antivirus products scan every file pip writes, which turns a 3-minute
install into 20. If installation crawls, add `C:\projects\mhms` to your
antivirus exclusions.

---

## Before your defence

Run through this the day before, not on the morning:

- [ ] Both terminals start cleanly from a fresh reboot
- [ ] `python src\test_system.py` ends with "all functional tests passed"
- [ ] `python service\test_api.py` ends with "40 passed, 0 failed"
- [ ] You can classify a sentence you make up on the spot
- [ ] You know how to restart the service if it stops (`Ctrl+C`, then run again)
- [ ] The project folder is backed up somewhere other than that laptop
