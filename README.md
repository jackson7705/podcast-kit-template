# podcast-kit

Turn the blog posts you already have into a podcast, and end up with an RSS feed URL you can
submit to Apple Podcasts, Spotify, and every other directory.

```
your blog  →  ingest  →  episode manifests  →  NotebookLM podcast  →  ffmpeg  →  feed.xml  →  a URL
```

- **No LLM API key.** Your own coding agent (Claude Code or Codex) picks the posts and writes
  the episode metadata. NotebookLM turns each post into a two-host conversation.
- **You own the feed.** Audio and `feed.xml` live on your domain, so you never get locked into
  a podcast host.
- **It checks itself.** `preflight.mjs` catches the feed problems that pass every validator and
  still get you rejected by Apple or Spotify.

Multiple shows have shipped through this pipeline and are live on Apple and Spotify. Most of
what is in here is the debugging, not the wiring.

---

## Step-by-step: your first show

Budget about an hour for the first show, most of it on hosting (Step 6). After that, a new
batch of episodes is a few minutes of your time.

### Step 0. What you need

| need | why | get it |
|---|---|---|
| A blog with an RSS feed, sitemap, or WordPress site | the source material | most sites have `/feed` |
| Node 18+ | runs the pipeline | <https://nodejs.org> |
| `ffmpeg` | mixes the audio | `brew install ffmpeg` (Mac) or `apt install ffmpeg` |
| Python 3.10+ and [`uv`](https://docs.astral.sh/uv/) | runs the NotebookLM client and the uploader | `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| A Google account | NotebookLM generates the audio | <https://notebooklm.google.com> |
| Claude Code or Codex | writes the episode files | <https://claude.com/claude-code> |
| A domain you control | hosts the feed (Step 6) | you probably have one already |

### Step 1. Get your own copy

Click **Use this template → Create a new repository** at the top of this page (make it private
if you like), then clone it:

```bash
git clone https://github.com/<you>/<your-podcast-repo>.git
cd <your-podcast-repo>
```

### Step 2. Hear the demo (2 minutes, no accounts)

```bash
cp demo/show.config.json .
cp demo/episodes/*.mdx episodes/
node generate.mjs
```

That renders a real episode and writes `output/feed.xml` using your Mac's built-in voice
(on Linux, install [Piper](https://github.com/rhasspy/piper) and set `PIPER_MODEL`).
It sounds robotic on purpose: you're hearing the *shape* of the show. When you're done, reset:

```bash
rm show.config.json episodes/*.mdx
rm -rf output
```

### Step 3. Describe your show

```bash
cp show.config.example.json show.config.json
cp .env.example .env
```

Open `show.config.json` and fill in every field. The keys starting with `_` are notes that
explain each field; read them, they come from real rejections. The ones that matter most:

- **`title`**: Apple and Spotify search is keyword-literal. "Phoenix Roofing Answers by Acme"
  gets found; "The Acme Show" has to earn it.
- **`itunesEmail`**: Spotify sends your ownership code here. Use an inbox you check.
- **`feedUrl`** and **`audioBaseUrl`**: where the show will live (decided in Step 6). Use
  placeholders for now if you haven't picked yet.
- **`episode.cta`**: the closing line of every episode. Who you are, where you work, where to go.

You also need **cover art**: a square PNG or JPEG, 1400 to 3000 px, RGB. Name it with a version,
like `cover-v1.png`, and bump the version any time you change it (Apple caches by filename).

### Step 4. Connect NotebookLM

```bash
uv tool install "notebooklm-py[browser] @ git+https://github.com/jackson7705/notebooklm-py.git"
notebooklm login                          # opens a browser; sign into Google
notebooklm auth check --test --passive    # should say you're signed in
```

This is an unofficial client that drives the NotebookLM website as you. Free accounts have a
daily Audio Overview limit, so plan on a handful of episodes per day.

### Step 5. Pull in your blog posts and create episodes

```bash
node ingest.mjs --from https://yoursite.com/feed --limit 20
```

That saves each post as plain text in `sources/`. Other sources work too:
`--from https://yoursite.com --source wordpress`, a `sitemap.xml` URL, or
`--from ./posts --source local`. Add `--list` to preview without saving.

Now open Claude Code or Codex in this folder and say:

> **Read AGENTS.md and create episode manifests 1 to 5 from sources/**

Your agent picks the five posts that make the best audio and writes one small file per episode
in `episodes/`. Look them over: titles and descriptions show up in every podcast app. Make sure
every `publishedAt` date is **in the past** (future dates make episodes silently disappear).

Then generate:

```bash
node setup-check.mjs          # tells you exactly what's missing, and how to fix it
node generate.mjs --dry-run   # checks the episode files without using NotebookLM quota
node generate.mjs             # creates the audio (several minutes per episode)
```

Listen to `output/` before going further.

### Step 6. Pick where the show lives

**Your feed URL is permanent.** Apple and Spotify check one URL for the life of the show, and
moving later is painful. Put it on a domain you control, like `podcast.yoursite.com`.

The easiest options:

- **Cloudflare R2** (recommended, basically free): create a bucket, connect a custom domain
  like `podcast.yoursite.com` to it, and create an API token with read/write on that bucket.
  Your domain's DNS needs to be on Cloudflare (the free plan is fine; you can keep your
  registrar). Fill the `R2_*` lines in `.env` and set `"host": { "provider": "r2" }`.
- **Bunny.net**: if you don't want to move DNS. One CNAME record. Fill the `BUNNY_*` lines.
- **Already on AWS**: `s3`, with a CDN in front.
- **Anything else**: `local` stages the files in `output/_upload/` for you to copy wherever.

Want it at `yoursite.com/podcast/` instead of a subdomain? See [worker/README.md](worker/README.md).

Then set `feedUrl`, `audioBaseUrl`, and `image` in `show.config.json` to that domain, and upload
your cover art to the same place.

### Step 7. Publish and check

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python publish.py all   # uploads audio, builds the feed against real URLs, uploads the feed
node preflight.mjs                # the important one
```

`preflight` only prints your feed URL once it would pass submission. If it complains, fix what
it says and re-run `publish.py all`.

### Step 8. Submit to the directories

Paste the feed URL from preflight into each of these. The first two matter most; the rest take
five minutes each.

| directory | where to submit | notes |
|---|---|---|
| Apple Podcasts | <https://podcastsconnect.apple.com> | Review takes 1 to 5 days. |
| Spotify | <https://creators.spotify.com> | Choose "I already have a podcast". Sends a code to `itunesEmail`. |
| YouTube Music | <https://studio.youtube.com> → Create → New podcast → RSS feed | |
| Amazon Music / Audible | <https://podcasters.amazon.com> | |
| iHeartRadio | <https://podcasters.iheart.com> | |
| Pandora | <https://amp.pandora.com> | |
| Podcast Index | <https://podcastindex.org/add> | Feeds many smaller apps automatically. |
| TuneIn, Castbox, Podchaser, Goodpods, Podcast Addict, Listen Notes | each site's "submit/claim podcast" page | Most pick you up from Podcast Index; claim them anyway. |

**Never pick an option that "migrates" or "imports" your show to their hosting.** You want
them to *read* your feed, not take it over. Keep a simple list of where you've submitted and
the listing URLs once they go live, then link them from your site's podcast page.

### Step 9. Add episodes later

Same loop, any time:

```bash
node ingest.mjs --from https://yoursite.com/feed --limit 20
```

> **Read AGENTS.md and create episode manifests 6 to 10 from sources/**

```bash
node generate.mjs && .venv/bin/python publish.py all && node preflight.mjs
```

Never change an episode's `slug` after it's published. That's how directories tell episodes apart.

Want it to run itself? See [Hands-off publishing](#optional-hands-off-publishing) below.

---

## Why NotebookLM is the default

Text-to-speech can only perform the words it receives. A better voice can make an article
sound nicer, but it cannot turn that article into a conversation. The `notebooklm` provider
sends the source material to NotebookLM as a whole and downloads its Audio Overview: hosts
explaining, reacting, and asking each other the questions a listener would ask.

Claude Code or Codex still chooses the source and writes the episode metadata against the
contract in [AGENTS.md](AGENTS.md). NotebookLM writes and performs the conversation from the
matching local source captured by `ingest.mjs`. Literal providers remain available only when
an exact approved script is required.

This uses the unofficial [`notebooklm-py`](https://github.com/jackson7705/notebooklm-py)
client (a pinned fork of [teng-lin/notebooklm-py](https://github.com/teng-lin/notebooklm-py)). It automates the signed-in NotebookLM product; it is
not an official Google API and can change when NotebookLM changes.

---

## preflight

Not an XML validator — [castfeedvalidator.com](https://castfeedvalidator.com) already tells
you whether the XML parses. Every check in `preflight.mjs` is something that **passes generic
validation and still breaks**, collected from feeds that actually failed:

- Every `<enclosure>` HEAD 200, `audio/*`, and `length` matching the real byte count. A
  mismatch means the feed was built before the last render — apps show the wrong duration
  or refuse to scrub.
- `<atom:link rel="self">` equals the URL you are submitting. Left stale after a host move,
  Podcasts Connect answers only *"An error has occurred. Try again later."*
- No `pubDate` in the future. Staggering a season forward hides every episode past today,
  and nothing tells you.
- Artwork reachable, square, 1400–3000px, RGB JPEG/PNG, and **HEAD allowed**.
- The feed URL serves XML, not an HTML error page. WordPress media rejects `.xml` uploads,
  which is how that one usually happens.
- `<itunes:email>` present — Spotify mails the ownership code there and there is no other way in.

It works on any feed URL, including ones podcast-kit did not build.

---

## Hosting

**Your feed URL is a one-way door.** Apple and Spotify poll one URL for the life of the
show. Moving later means a change-of-address dance and risking the listing. So put it on a
domain you control on day one — this is the decision to spend ten minutes on.

| provider | when |
|---|---|
| **`r2`** | **Default.** Cloudflare R2 with a custom domain. Zero egress fees, which is exactly the shape of podcast hosting, and overwrite-in-place keeps every URL stable. The domain must be a zone in the same Cloudflare account — you can keep it registered at GoDaddy or Namecheap and just point the nameservers at Cloudflare's free plan. |
| `bunny` | You would rather not move nameservers. Bunny issues a hostname you point one CNAME at. |
| `s3` | You are already on AWS. Put a CDN in front or egress will cost you. |
| `local` | Stages to `output/_upload/`; copy it anywhere. |

Not recommended for a real show: the `r2.dev` development URL, which Cloudflare
[rate-limits and marks as non-production](https://developers.cloudflare.com/r2/buckets/public-buckets/),
and any `*.github.io` host — a URL you will want to leave.

---

## Optional: hands-off publishing

`automation/` is an unattended mode for when the show is up and running. It checks daily and
publishes one episode every `PUBLISH_INTERVAL_DAYS` (default two) from your whole blog archive,
newest unpublished post first, so new posts go next and the backlog drains in between.

It runs as a container (`Dockerfile.automation`) on any host with a scheduler and a persistent
volume, such as Railway, Render, or Fly. Setup:

1. Edit `automation/show.config.json` for your show (same fields as Step 3). Commit it.
2. On your machine, run `notebooklm login --master-token --account you@gmail.com`, then copy
   the contents of `~/.notebooklm/profiles/default/master_token.json` into the host's secret
   `NOTEBOOKLM_MASTER_TOKEN_JSON`. Unlike browser cookies, this token doesn't expire every
   week or two. Treat it like a
   password: it is a login to your Google account.
3. Set the other secrets from the "Scheduled automation" section of `.env.example`: at least
   `BLOG_FEED_URL`, your host's `R2_*` (or other host) credentials, and `AUTOMATION_TIME_ZONE`.
4. Mount a persistent volume at `/data` and schedule `python3 automation/maintain.py` every
   twenty minutes (`*/20 * * * *`).

What it does each run: refreshes NotebookLM login, publishes at most once per day after 9 AM
in your time zone, runs preflight against the live feed, and restores the previous `feed.xml`
automatically if preflight fails. The live feed plus a run history in your bucket prevent
duplicate episodes. A failed or uncertain publication blocks later days until you check the
live feed and rerun `node automation/weekly.mjs --force-schedule` yourself.
`--ignore-cadence` publishes immediately for a manual catch-up.

A watchdog also checks outcomes, not just errors: it flags `stale-feed` when nothing has
published for `PUBLISH_INTERVAL_DAYS` or more, and `backlog-low` when fewer than
`BACKLOG_ALERT_THRESHOLD` (default ten) usable posts remain. With `AUTOMATION_EMAIL_ALERTS=1`,
those alerts and failures are emailed through the [Composio](https://composio.dev) CLI's Gmail
connection (`ALERT_TO_EMAIL`, `ALERT_FROM_EMAIL`, `COMPOSIO_USER_DATA_JSON`), at most once per
stage per day. Alerts need the container to start, so they cannot detect the host itself being down.

Never upload the NotebookLM cookie or token files to your public podcast bucket.

---

## Audio providers

NotebookLM is the default provider for real shows. The
others are explicit literal-TTS fallbacks.

| provider | for |
|---|---|
| **`notebooklm`** | **Default conversational podcast.** Creates a grounded Audio Overview from the matching ingested source. |
| `local` | Zero setup. [Piper](https://github.com/rhasspy/piper) via `PIPER_MODEL`, else macOS `say` via `SAY_VOICE` (`say -v "?"` lists them). |
| `command` | **Any local model with a CLI.** |
| `openai` | **Any OpenAI-compatible `/v1/audio/speech` server**, which is what most local TTS servers expose. |
| `elevenlabs` | Legacy literal hosted TTS for an explicitly approved script. |

### NotebookLM Audio Overviews

```json
"tts": {
  "provider": "notebooklm",
  "format": "deep-dive",
  "length": "default",
  "language": "en",
  "timeout": 1200,
  "retry": 2,
  "instructions": "Make this a lively conversation. Stay grounded in the source."
}
```

For each episode, podcast-kit matches `sourceArticle` to `sources/index.json`, uploads that
local text, generates the conversation, and downloads the exact returned artifact ID. Local
use reads the session created by `notebooklm login`; CI and scheduled hosts use the same storage-state
JSON through the secret `NOTEBOOKLM_AUTH_JSON`. Treat it as a bearer credential and never
commit or print it.

There is no "voice id" for a local model. Piper takes a path to a `.onnx` file you
downloaded; `say` takes the name of a voice on the machine; Kokoro takes a voice name baked
into the model. None of it is a secret or tied to an account.

### Using any local model — `command`

```json
"tts": {
  "provider": "command",
  "command": "kokoro-tts {{text_file}} {{out}} --voice af_heart",
  "outputFormat": "wav"
}
```

`{{text_file}}` is a temp file holding one paragraph, `{{out}}` is where your tool must write
audio, `{{text}}` inlines the text shell-quoted instead. Use none of them and the text
arrives on stdin. Whatever format your tool writes gets converted to mp3 here. The command
runs through `sh -c`, so pipes work.

That is the whole integration. No adapter, no PR, no wait for this repo to catch up with a
model list that turns over every few months.

### Using a local server — `openai`

```json
"tts": {
  "provider": "openai",
  "baseUrl": "http://localhost:8880/v1",
  "model": "kokoro",
  "voice": "af_heart"
}
```

Works against Kokoro-FastAPI, LocalAI, Speaches, or OpenAI itself. Set `TTS_API_KEY` only if
your endpoint wants one; a local server usually does not.

### Which local model

**Check the license before you ship a commercial show** — this is where people get caught,
not on quality. As widely reported (verify on the model card yourself, licenses change):

| model | license | notes |
|---|---|---|
| **Kokoro-82M** | Apache 2.0 | The usual default. 82M params, runs on a laptop CPU, many voices. |
| **Piper** | MIT | Fast, small, lots of prebuilt voices. Has a first-class provider here. |
| **Chatterbox** | MIT | Does voice cloning, permissively licensed. Wants a GPU. |
| **StyleTTS 2** | MIT | Strong quality, more setup. |
| **XTTS v2** | ⚠️ CPML — **non-commercial** | Coqui shut down in 2024. Good at cloning, and the most common licensing mistake in this space. |
| **F5-TTS** | ⚠️ CC-BY-NC — **non-commercial** | Same trap. |

Not TTS at all, despite showing up in "local speech models" lists: **Whisper** and **NVIDIA
Parakeet** are speech-*to*-text.

---

## Things this repo knows that cost someone a day

- **NotebookLM artifacts need exact IDs.** Downloading "latest" from a reused notebook can
  select the wrong episode after eventual-consistency delays. The task ID is carried into
  the download command.
- **Literal TTS drifts on long calls.** Those providers still synthesize per paragraph,
  level-match the chunks, and join them with a short beat.
- **Two voice clones do not render at the same loudness.** Two measured on identical
  settings came out 6.5 dB apart, and the quieter one sat underneath its own theme music.
  So the mix measures the voice and lifts it to a target instead of trusting a fixed gain.
- **Music overlaps and ducks; it never hard-cuts.** The intro plays solo, then fades under
  the first line. `overlapIn`/`overlapOut` in config are tuned to the fade envelopes in the
  music itself — change one, change the other.
- **Version your artwork filename.** Apple caches art by filename, and a CDN in front of
  your bucket keeps serving the old object after you overwrite the key. Bump `-vN`; do not
  trust a purge.
- **Never publish an episode at a URL that can collide with an existing page.** Slug
  collisions on a CMS overwrite live pages.

---

## Layout

```
AGENTS.md              the writing contract — your agent reads this
show.config.json       everything show-specific. No show detail belongs in code.
pronunciations.json    spoken-form fixes applied to TTS input only
voice.md               optional: your show's register, read by the writing step

ingest.mjs   ingest/   posts → sources/*.txt      (rss · sitemap · wordpress · local)
             episodes/ *.mdx                       ← written by your agent
gates/       check.py  the failing test
generate.mjs tts/      NotebookLM/TTS → mix → output/feed.xml
publish.py   hosts/    upload + rebuild feed       (r2 · bunny · s3 · local)
preflight.mjs          validate the live feed, print the URL
```



---

MIT licensed. Contributions welcome, particularly host and TTS adapters.
