#!/bin/bash
# release-state.sh — read-only snapshot of one app's release state: version everywhere, tag,
# GitHub release, Homebrew tap, README/wiki/CHANGELOG, Ko-fi, local install, last stamp.
#
#   release-state.sh [repo-dir]            report (default: current dir)
#   release-state.sh [repo-dir] --stamp    record "finalized" for the current state
#
# Prints OK / GAP / WARN / INFO lines and a summary. Always exits 0 — it reports, the agent decides.
# Only network/side effects: `git fetch --tags`, `git ls-remote`, `gh` reads.
# Overrides: APPS_ROOT (where personal apps live), TAP_WORK (tap working copy), FAR_STATE_DIR (stamp dir).

OWNER=roypadina
TAP_SLUG=$OWNER/homebrew-tap
TAP_WORK=${TAP_WORK:-$HOME/Code/Padina/homebrew-tap}
APPS_ROOT=${APPS_ROOT:-$HOME/Code/Padina}
KOFI="ko-fi.com/$OWNER"
STATE_DIR=${FAR_STATE_DIR:-${XDG_STATE_HOME:-$HOME/.local/state}/finalize-app-release}

STAMP=0; DIR=.
for a in "$@"; do case $a in --stamp) STAMP=1 ;; *) DIR=$a ;; esac; done

GAPS=0; WARNS=0
ok()   { echo "OK    $*"; }
gap()  { echo "GAP   $*"; GAPS=$((GAPS+1)); }
warn() { echo "WARN  $*"; WARNS=$((WARNS+1)); }
info() { echo "INFO  $*"; }

R=$(git -C "$DIR" rev-parse --show-toplevel 2>/dev/null) || { echo "not a git repo: $DIR"; exit 0; }
cd "$R" || exit 0
TOKEN=$(env -u GITHUB_TOKEN command gh auth token -u $OWNER 2>/dev/null)
GH() { env -u GITHUB_TOKEN GH_TOKEN="$TOKEN" command gh "$@"; }

# ---------- repo ----------
REMOTE=$(git remote -v | awk -v o="$OWNER/" 'index($2,o) && /\(push\)/ {print $1; exit}')
SLUG=""; VIS=""
if [ -n "$REMOTE" ]; then
  SLUG=$(git remote get-url "$REMOTE" | sed -E "s#.*[:/]$OWNER/([^/]+)\$#\\1#; s#\\.git\$##")
  VIS=$(GH repo view "$OWNER/$SLUG" --json visibility -q .visibility 2>/dev/null)
fi
# Personal apps only: a repo under APPS_ROOT, pushed to the personal account, that is in the tap or
# looks like a Mac app (a new one headed there). Anything else → SKIP, so callers can run it blindly.
case "$R/" in "$APPS_ROOT"/*) ;; *) echo "SKIP  $R is not under $APPS_ROOT — not a personal app"; exit 0 ;; esac
[ -z "$REMOTE" ] && { echo "SKIP  no $OWNER/* remote — not on the personal GitHub account"; exit 0; }
case $SLUG in homebrew-tap|*.wiki) echo "SKIP  $SLUG is not an app repo"; exit 0 ;; esac
grep -qisE "github\.com/$OWNER/$SLUG([/\"]|\.git)" "$TAP_WORK"/Casks/*.rb "$TAP_WORK"/Formula/*.rb 2>/dev/null \
  || ls Package.swift ./*.xcodeproj Info.plist >/dev/null 2>&1 \
  || { echo "SKIP  $OWNER/$SLUG is not in the tap and has no Mac app project"; exit 0; }
BRANCH=$(git branch --show-current)
echo "== $(basename "$R")  repo=$OWNER/$SLUG remote=$REMOTE visibility=${VIS:-?} branch=$BRANCH"

DIRTY=$(git status --porcelain | wc -l | tr -d ' ')
[ "$DIRTY" = 0 ] && ok "working tree clean" || warn "working tree: $DIRTY uncommitted/untracked path(s)"

if [ -n "$REMOTE" ]; then
  git fetch -q --tags "$REMOTE" 2>/dev/null
  SRV=$(git ls-remote "$REMOTE" "refs/heads/$BRANCH" 2>/dev/null | cut -f1)
  if [ -z "$SRV" ]; then warn "branch $BRANCH not on $REMOTE"
  elif [ "$SRV" = "$(git rev-parse HEAD)" ]; then ok "$BRANCH pushed (server = HEAD)"
  else gap "$BRANCH differs from server ($REMOTE): unpushed or behind"; fi
  [ "$BRANCH" != main ] && warn "on branch $BRANCH, releases ship from main"
  EMAIL=$(git config user.email)
  case $EMAIL in *@users.noreply.github.com) ok "commit email is the GitHub noreply address" ;;
    *) gap "commit email '$EMAIL' — GitHub email privacy rejects the push; set the repo-local noreply address" ;; esac
fi

# ---------- version ----------
pl() { /usr/libexec/PlistBuddy -c "Print $1" "$2" 2>/dev/null; }
VER=""; VSRC=""
if [ -f package.json ]; then
  VER=$(sed -nE 's/^  "version": "([^"]+)".*/\1/p' package.json | head -1); VSRC=package.json
fi
if [ -z "$VER" ]; then
  f=$(grep -lsE '^[[:space:]]*MARKETING_VERSION[[:space:]]*=' Config/*.xcconfig ./*.xcconfig | head -1)
  [ -n "$f" ] && VER=$(sed -nE 's/^[[:space:]]*MARKETING_VERSION[[:space:]]*=[[:space:]]*([^[:space:];]+).*/\1/p' "$f" | head -1) VSRC=$f
fi
if [ -z "$VER" ]; then
  for f in Scripts/package_app.sh build.sh Scripts/build.sh; do
    [ -f "$f" ] || continue
    VER=$(sed -nE 's/^[[:space:]]*(APP_)?VERSION="?([0-9][^"[:space:]]*)"?.*/\2/p' "$f" | head -1)
    [ -z "$VER" ] && VER=$(grep -A1 CFBundleShortVersionString "$f" | sed -nE 's#.*<string>([0-9][^<]*)</string>.*#\1#p' | head -1)
    [ -n "$VER" ] && { VSRC=$f; break; }
  done
fi
if [ -z "$VER" ]; then
  for f in Info.plist; do
    v=$(pl CFBundleShortVersionString "$f"); case $v in [0-9]*) VER=$v VSRC=$f; break ;; esac
  done
fi
if [ -z "$VER" ]; then
  f=$(ls ./*.xcodeproj/project.pbxproj 2>/dev/null | head -1)
  [ -n "$f" ] && VER=$(sed -nE 's/.*MARKETING_VERSION = ([0-9][^;]*);.*/\1/p' "$f" | sort | uniq -c | sort -rn | awk 'NR==1{print $2}') VSRC=$f
fi
if [ -n "$VER" ]; then info "source version $VER ($VSRC)"
elif [ "$VIS" = PUBLIC ]; then gap "source version not found — locate it by hand"
else info "no version found (unversioned private tool?)"; fi

LATEST=$(git tag -l 'v[0-9]*' | sed 's/^v//' | sort -V | tail -1)
if [ -n "$VER" ]; then
  if git rev-parse -q --verify "refs/tags/v$VER" >/dev/null; then
    AHEAD=$(git rev-list --count "v$VER"..HEAD)
    ok "tag v$VER exists"
    [ "$AHEAD" -gt 0 ] && warn "$AHEAD commit(s) on HEAD since v$VER — unreleased changes (bump + release?)"
    PREV=$(git tag -l 'v[0-9]*' | sed 's/^v//' | sort -V | grep -B1 -x "$VER" | head -1); [ "$PREV" = "$VER" ] && PREV=""
  else
    [ -n "$REMOTE" ] && gap "tag v$VER missing (latest tag: ${LATEST:-none}) — release not cut"
    PREV=$LATEST
  fi
fi

# ---------- GitHub release ----------
REL_TAG=""; REL_DATE=""; ASSETS=""
if [ -n "$SLUG" ]; then
  J=$(GH release view --repo "$OWNER/$SLUG" --json tagName,publishedAt,assets \
       -q '.tagName+" "+.publishedAt+" "+([.assets[]|.name+"="+(.digest//"")]|join(","))' 2>/dev/null)
  read -r REL_TAG REL_DATE ASSETS <<<"$J"
  if [ -z "$REL_TAG" ]; then [ "$VIS" = PUBLIC ] && gap "no GitHub release"
  elif [ "$REL_TAG" = "v$VER" ]; then ok "GitHub release $REL_TAG (${REL_DATE%%T*}) assets: $(echo "${ASSETS:-none}" | sed -E 's/=[^,]*//g')"
  else gap "latest GitHub release $REL_TAG ≠ source v$VER"; fi
fi

# ---------- tap ----------
TOKEN_RB=""; KIND=""; APP=""
if [ -n "$SLUG" ] && [ -d "$TAP_WORK" ]; then
  RB=$(grep -lisE "github\\.com/$OWNER/$SLUG([/\"]|\\.git)" "$TAP_WORK"/Casks/*.rb "$TAP_WORK"/Formula/*.rb 2>/dev/null | head -1)
  if [ -n "$RB" ]; then
    TOKEN_RB=$(basename "$RB" .rb); KIND=$(basename "$(dirname "$RB")")
    URL=$(sed -nE 's/^[[:space:]]*url "([^"]+)".*/\1/p' "$RB" | head -1)
    SHA=$(sed -nE 's/^[[:space:]]*sha256 "([0-9a-f]+)".*/\1/p' "$RB" | head -1)
    if [ "$KIND" = Casks ]; then
      CV=$(sed -nE 's/^[[:space:]]*version "([^"]+)".*/\1/p' "$RB" | head -1)
      APP=$(sed -nE 's/^[[:space:]]*app "([^"]+)\.app".*/\1/p' "$RB" | head -1)
      ASSET=$(basename "$URL")
      case ",$ASSETS," in
        *",$ASSET=sha256:$SHA,"*) ok "cask url asset $ASSET + sha256 match the release" ;;
        *",$ASSET="*)             gap "cask sha256 ≠ release asset $ASSET digest" ;;
        *)                        [ -n "$REL_TAG" ] && gap "cask url asset '$ASSET' not in release $REL_TAG (assets: ${ASSETS%%=*})" ;;
      esac
    else
      CV=$(echo "$URL" | sed -nE 's#.*/v?([0-9][^/]*)\.tar\.gz$#\1#p')
    fi
    [ "$CV" = "$VER" ] && ok "tap $KIND/$TOKEN_RB.rb at $CV" || gap "tap $KIND/$TOKEN_RB.rb at ${CV:-?}, source $VER"
    grep -q "\*\*$TOKEN_RB\*\*" "$TAP_WORK/README.md" && ok "tap README lists $TOKEN_RB" || gap "tap README has no row for $TOKEN_RB"
    TSRV=$(git ls-remote "https://github.com/$TAP_SLUG.git" refs/heads/main 2>/dev/null | cut -f1)
    [ "$(git -C "$TAP_WORK" rev-parse HEAD)" = "$TSRV" ] && ok "tap working copy = server" \
      || gap "tap working copy ≠ server main (unpushed, or needs pull)"
    [ -n "$(git -C "$TAP_WORK" status --porcelain)" ] && gap "tap working copy has uncommitted changes"
    TB=$(brew --repository "$TAP_SLUG" 2>/dev/null)
    [ -d "$TB/.git" ] && { [ "$(git -C "$TB" rev-parse HEAD)" = "$TSRV" ] && ok "brew's tap clone = server" \
      || warn "brew's tap clone ≠ server (brew update)"; }
  elif [ "$VIS" = PUBLIC ]; then
    gap "public repo, no cask/formula in $TAP_SLUG ($TAP_WORK)"
  else
    info "not in the tap (repo ${VIS:-?})"
  fi
fi

# ---------- docs ----------
if [ -f CHANGELOG.md ]; then
  CL=$(grep -m1 -E '^## \[?v?[0-9]' CHANGELOG.md | sed -E 's/^## \[?v?([0-9][^] ]*).*/\1/')
  [ "$CL" = "$VER" ] && ok "CHANGELOG top entry $CL" || gap "CHANGELOG top entry ${CL:-none} ≠ $VER"
elif [ "$VIS" = PUBLIC ]; then
  gap "no CHANGELOG.md"
else
  warn "no CHANGELOG.md"
fi
if [ -f appcast.xml ]; then
  AC=$(grep -m1 -oE 'shortVersionString="[^"]+"' appcast.xml | cut -d'"' -f2)
  [ "$AC" = "$VER" ] && ok "appcast.xml top item $AC" || gap "appcast.xml top item ${AC:-none} ≠ $VER"
fi
[ -f README.md ] || gap "no README.md"
if [ -n "$TOKEN_RB" ] && [ -f README.md ]; then
  CMD="brew install $( [ "$KIND" = Casks ] && echo '--cask ')$OWNER/tap/$TOKEN_RB"
  grep -qE "$OWNER/tap/$TOKEN_RB|install (--cask )?$TOKEN_RB" README.md && ok "README has the brew install line" \
    || gap "README lacks '$CMD'"
fi

# ---------- wiki ----------
WIKI=""
for w in "$R/wiki" "$(dirname "$R")/$SLUG.wiki" "$(dirname "$R")/$(basename "$R").wiki"; do
  [ -n "$SLUG" ] && git -C "$w" remote -v 2>/dev/null | grep -q '\.wiki' && { WIKI=$w; break; }
done
WSRV=""
[ -n "$SLUG" ] && WSRV=$(git ls-remote "https://github.com/$OWNER/$SLUG.wiki.git" HEAD 2>/dev/null | cut -f1)
if [ -n "$SLUG" ] && [ -z "$WSRV" ]; then
  [ "$VIS" = PUBLIC ] && gap "GitHub wiki not initialised — the user must create the first page in the web UI (no API)"
elif [ -n "$WSRV" ] && [ -z "$WIKI" ]; then
  gap "wiki live on GitHub but no local clone (clone github-padina:$OWNER/$SLUG.wiki.git next to the repo)"
elif [ -n "$WIKI" ]; then
  [ -n "$(git -C "$WIKI" status --porcelain)" ] && gap "wiki clone $WIKI has uncommitted changes"
  [ "$(git -C "$WIKI" rev-parse HEAD)" = "$WSRV" ] && ok "wiki pushed (server = local)" || gap "wiki local ≠ server — push (by URL) or pull"
  WD=$(git -C "$WIKI" log -1 --format=%cs)
  [ -n "$REL_DATE" ] && [[ "$WD" < "${REL_DATE%%T*}" ]] && warn "wiki last changed $WD, before release ${REL_DATE%%T*} — review pages for the new version"
fi

# ---------- stale version strings ----------
if [ -n "$PREV" ]; then
  HITS=$( { git grep -nF "$PREV" -- '*.md' '*.yml' '*.yaml' '*.html' ':!CHANGELOG.md' ':!**/CHANGELOG.md' 2>/dev/null
            [ -n "$WIKI" ] && git -C "$WIKI" grep -nF "$PREV" -- '*.md' 2>/dev/null | sed 's#^#wiki/#'; } | head -12)
  [ -n "$HITS" ] && warn "previous version $PREV still mentioned (stale, or a legit 'since $PREV' note?):" && echo "$HITS" | sed 's/^/        /'
fi

# ---------- Ko-fi (public repos) ----------
if [ "$VIS" = PUBLIC ]; then
  grep -q "$KOFI" README.md 2>/dev/null && grep -q 'img.shields.io/badge/Ko--fi' README.md && grep -q '^## Support' README.md \
    && ok "README Ko-fi badge + ## Support" || gap "README Ko-fi incomplete (shields badge in header + '## Support' with the button)"
  grep -qs "ko_fi: $OWNER" .github/FUNDING.yml && ok ".github/FUNDING.yml ko_fi" || gap ".github/FUNDING.yml missing 'ko_fi: $OWNER'"
  if [ -n "$WIKI" ]; then
    m=""; for p in _Sidebar.md _Footer.md Home.md; do grep -qs "$KOFI" "$WIKI/$p" || m="$m $p"; done
    [ -z "$m" ] && ok "wiki Ko-fi in _Sidebar/_Footer/Home" || gap "wiki Ko-fi missing in:$m"
  fi
  SRC=$(git grep -lF "$KOFI" -- ':!*.md' ':!.github' ':!*.yml' 2>/dev/null | head -3 | tr '\n' ' ')
  [ -n "$SRC" ] && ok "in-app Ko-fi link: $SRC" || gap "no Ko-fi link in app source (About window / menu / --help)"
fi

# ---------- local install ----------
if [ -n "$APP" ] && [ "$KIND" = Casks ]; then
  A="/Applications/$APP.app"
  if [ -d "$A" ]; then
    LV=$(pl CFBundleShortVersionString "$A/Contents/Info.plist")
    [ "$LV" = "$VER" ] && ok "installed $A is $LV" || gap "installed $A is $LV, source $VER — upgrade the local install"
    xattr -p com.apple.quarantine "$A" >/dev/null 2>&1 && warn "$A still quarantined (xattr -dr com.apple.quarantine)"
    EXE=$(pl CFBundleExecutable "$A/Contents/Info.plist")
    PIDS=$(pgrep -x "$EXE" | tr '\n' ' ')
    if [ -z "$PIDS" ]; then warn "$EXE not running"
    else for p in $PIDS; do C=$(ps -o comm= -p "$p"); case $C in "$A"/*) ok "running pid $p from /Applications" ;;
      *) warn "pid $p runs from $C (not /Applications)" ;; esac; done
      [ "$(echo $PIDS | wc -w)" -gt 1 ] && warn "more than one $EXE running"
    fi
  else
    gap "$A not installed"
  fi
  BV=$(brew list --cask --versions "$TOKEN_RB" 2>/dev/null | awk '{print $2}')
  [ -n "$BV" ] && [ "$BV" != "$VER" ] && info "brew records $TOKEN_RB $BV (fine only if this app is installed another way on purpose)"
elif [ "$KIND" = Formula ]; then
  BV=$(brew list --versions "$TOKEN_RB" 2>/dev/null | awk '{print $2}')
  [ "$BV" = "$VER" ] && ok "brew formula $TOKEN_RB $BV installed" || gap "brew formula $TOKEN_RB is ${BV:-not installed}, source $VER"
fi

# ---------- stamp ----------
FP="v$VER head=$(git rev-parse --short HEAD) wiki=$( [ -n "$WIKI" ] && git -C "$WIKI" rev-parse --short HEAD || echo -) tap=${CV:--}"
SF="$STATE_DIR/$(basename "$R")"
if [ $STAMP = 1 ]; then
  mkdir -p "$STATE_DIR" && echo "$FP $(date +%F)" > "$SF" && info "stamped: $FP"
  [ $GAPS -gt 0 ] && warn "stamped with $GAPS open GAP(s) — only right if the user accepted them"
elif [ -f "$SF" ] && [ "$(cut -d' ' -f1-4 "$SF")" = "$FP" ]; then
  info "STAMP MATCH — finalized on $(cut -d' ' -f5 "$SF"), nothing changed since (repo, wiki, tap)"
else
  info "stamp: ${SF/#$HOME/~} $( [ -f "$SF" ] && echo "is stale ($(cat "$SF"))" || echo "none")"
fi
echo "== $GAPS GAP, $WARNS WARN"
exit 0
