#!/usr/bin/env bash
# The body of .github/workflows/grid-accounts.yml: one control-panel action on the grid's Claude
# accounts, said to the grid's ssh gate as its accounts words, with the answer written to the branch
# grid for the panel (tools/grid_accounts.py masks it; a sign-in link is sealed for the panel's key and
# never printed). Reads its inputs from the environment the workflow sets.
set -euo pipefail
case "$ACTION" in list|use|login|code|usage|auto-on|auto-off|forget|worker-start|worker-stop) ;; *) echo "::error::unknown action $ACTION"; exit 1;; esac
case "$ACTION" in use|login|code|forget|worker-start)
  [[ "$SLOT" =~ ^([1-9]|[12][0-9]|3[0-2])$ ]] || { echo "::error::the account is a number from 1 to 32"; exit 1; };;
esac
NAME=${NAME:-}
case "$ACTION" in
  worker-start) [[ "$NAME" =~ ^[A-Za-z0-9_-]{0,24}$ ]] || { echo "::error::a worker's name is up to 24 letters, digits, _ or -"; exit 1; };;
  worker-stop) [[ "$NAME" =~ ^[A-Za-z0-9_-]{1,32}$ ]] || { echo "::error::name the worker to stop"; exit 1; };;
esac
[[ "$REQUEST" =~ ^[A-Za-z0-9_-]{0,64}$ ]] || { echo "::error::the request is a short plain name"; exit 1; }
if [ "$ACTION" = code ]; then
  [ -n "$CODE" ] && echo "::add-mask::$CODE"
  [[ "$CODE" =~ ^[A-Za-z0-9_#.~-]{8,512}$ ]] || { echo "::error::that is not a code Anthropic's page shows"; exit 1; }
fi
[ -n "$KEY" ] && [ -n "$ACCESS_ID" ] && [ -n "$HOST_KEY" ] \
  || { echo "::error::the environment grid needs the secret GRID_GATE_KEY and the variables GRID_ACCESS_ID and GRID_HOST_KEY (docs/setup/grid.md, The ssh gate)"; exit 1; }
[[ "$ACCESS_ID" =~ ^[A-Za-z0-9._-]+$ ]] || { echo "::error::GRID_ACCESS_ID is not a plain name"; exit 1; }

d=$(mktemp -d "${RUNNER_TEMP:-/tmp}/grid-accounts.XXXXXX")
trap 'rm -rf "$d"' EXIT
( umask 077; printf '%s\n' "$KEY" | tr -d '\r' > "$d/key"; printf '%s\n' "$HOST_KEY" | tr -d '\r' > "$d/known_hosts" )
unset KEY

# say WORD [STDIN_TEXT]: one call to the gate, its whole answer in $d/out, never echoed; one more
# try when the gate's floor refused it, after the seconds it named
say() {
  local rc=0 wait
  for _ in 1 2; do
    rc=0
    printf '%s' "${2:-}" | ssh -T -i "$d/key" -o IdentitiesOnly=yes -o BatchMode=yes -o PreferredAuthentications=publickey \
      -o StrictHostKeyChecking=yes -o UserKnownHostsFile="$d/known_hosts" -o GlobalKnownHostsFile=/dev/null \
      -o ConnectTimeout=30 -o LogLevel=ERROR "$ACCESS_ID@$HOST" "$1" > "$d/out" 2>&1 || rc=$?
    [ "$rc" = 123 ] || break
    wait=$(grep -o 'try again in [0-9]*' "$d/out" | grep -o '[0-9]*$' || echo 60)
    sleep $(( ${wait:-60} + 1 ))
  done
  # what the log shows: the gate's own words, e-mails masked; never the list or a link
  python3 tools/grid_accounts.py record "$d/said.json" --action "$ACTION" --rc "$rc" < "$d/out"
  python3 -c 'import json,sys; [print(l) for l in json.load(open(sys.argv[1]))["said"]]' "$d/said.json"
  return "$rc"
}

# publish: accounts.json (and link.json when there is one) on the branch grid, as one commit
publish() {
  local rc="$1" w="$d/branch" tries
  python3 tools/grid_accounts.py record "$d/accounts.json" --action "$ACTION" --slot "$SLOT" --request "$REQUEST" --rc "$rc" < "$d/out"
  for tries in 1 2 3 4; do
    rm -rf "$w"; git init -q "$w"
    git -C "$w" remote add origin "https://x-access-token:${GH_TOKEN}@github.com/${REPO}.git"
    if git -C "$w" fetch -q --depth 1 origin grid 2>/dev/null; then git -C "$w" checkout -q -b grid FETCH_HEAD; else git -C "$w" checkout -q --orphan grid; fi
    cp "$d/accounts.json" "$w/accounts.json"
    [ -s "$d/link.json" ] && cp "$d/link.json" "$w/link.json"
    [ -s "$w/README.md" ] || printf '%s\n' "# The grid's Claude accounts" "" "Written by .github/workflows/grid-accounts.yml for the control panel's Grid tab; e-mails are masked and a sign-in link is only ever here sealed for the browser that asked." > "$w/README.md"
    git -C "$w" add -A
    git -C "$w" -c user.name="github-actions[bot]" -c user.email="41898282+github-actions[bot]@users.noreply.github.com" commit -q -m "grid accounts: $ACTION ${SLOT}" || return 0
    git -C "$w" push -q origin grid 2>/dev/null && return 0
    sleep $(( tries * 2 ))
  done
  echo "::warning::could not write the branch grid"
}

# seal URL for the panel's RSA-OAEP public key: AES-256-CBC for the link, the AES key wrapped by RSA-OAEP-SHA256
seal_link() {
  local url="$1" aes iv data wrapped
  [[ "$PANEL_KEY" =~ ^[A-Za-z0-9+/=]{200,1400}$ ]] || { echo "::warning::no key to seal the sign-in link for; the panel asks again"; return 1; }
  printf '%s' "$PANEL_KEY" | base64 -d > "$d/panel.der"
  openssl pkey -pubin -inform DER -in "$d/panel.der" -out "$d/panel.pem" 2>/dev/null || { echo "::warning::the panel's key is not an RSA public key"; return 1; }
  aes=$(openssl rand -hex 32); iv=$(openssl rand -hex 16)
  data=$(printf '%s' "$url" | openssl enc -aes-256-cbc -K "$aes" -iv "$iv" | base64 -w0)
  wrapped=$(printf '%s' "$aes" | python3 -c 'import sys; sys.stdout.buffer.write(bytes.fromhex(sys.stdin.read()))' \
    | openssl pkeyutl -encrypt -pubin -inkey "$d/panel.pem" -pkeyopt rsa_padding_mode:oaep -pkeyopt rsa_oaep_md:sha256 -pkeyopt rsa_mgf1_md:sha256 | base64 -w0)
  python3 -c 'import json,sys,time; json.dump({"v":1,"request":sys.argv[1],"slot":sys.argv[2],"at":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime()),"sealed":{"key":sys.argv[3],"iv":sys.argv[4],"data":sys.argv[5]}},open(sys.argv[6],"w"))' \
    "$REQUEST" "$SLOT" "$wrapped" "$(printf '%s' "$iv" | python3 -c 'import base64,sys; print(base64.b64encode(bytes.fromhex(sys.stdin.read())).decode())')" "$data" "$d/link.json"
}

state() { python3 tools/grid_accounts.py state "$d/accounts.json" "$SLOT"; }
rc=0
case "$ACTION" in
  list) say accounts || rc=$?;;
  use) say "accounts use $SLOT" || rc=$?;;
  forget) say "accounts forget $SLOT" || rc=$?;;
  # the start and stop words print no list, so the list follows for the panel to show the worker
  worker-start) say "accounts start $SLOT${NAME:+ $NAME}" || rc=$?; [ "$rc" != 0 ] || { sleep 4; say accounts || true; };;
  worker-stop) say "accounts stop $NAME" || rc=$?; [ "$rc" != 0 ] || { sleep 4; say accounts || true; };;
  auto-on) say "accounts auto on" || rc=$?;;
  auto-off) say "accounts auto off" || rc=$?;;
  usage)
    say "accounts usage" || rc=$?
    publish "$rc"
    # the job reads each account in turn; the list once it has ended (at most about four minutes)
    for _ in $(seq 1 30); do
      python3 tools/grid_accounts.py usage-running "$d/accounts.json" || break
      sleep 8; say accounts || true
      python3 tools/grid_accounts.py record "$d/accounts.json" --action "$ACTION" < "$d/out"
    done;;
  login)
    say "accounts login $SLOT" || rc=$?
    publish "$rc"
    # the sitting's job prints Anthropic's link once it has a computer: asked for every few seconds,
    # for about three minutes, and sealed the moment it comes
    for _ in $(seq 1 45); do
      python3 tools/grid_accounts.py record "$d/accounts.json" --action "$ACTION" --slot "$SLOT" < "$d/out"
      case "$(state)" in failed|signed-in) break;; esac
      if say "accounts link $SLOT" > /dev/null; then
        url=$(python3 tools/grid_accounts.py link < "$d/out" || true)
        if [ -n "$url" ]; then echo "::add-mask::$url"; seal_link "$url" || true; url=""; break; fi
      fi
      sleep 4
    done
    rc=0;;
  code)
    say "accounts code $SLOT" "$CODE"$'\n' || rc=$?
    CODE=""
    for _ in $(seq 1 12); do
      python3 tools/grid_accounts.py record "$d/accounts.json" --action "$ACTION" --slot "$SLOT" < "$d/out"
      [ "$(state)" = code ] || break
      sleep 5; say accounts > /dev/null || true
    done;;
esac
publish "$rc"
{ echo "### The grid's Claude accounts: $ACTION ${SLOT}"; echo '```'; python3 -c 'import json,sys; [print(l) for l in json.load(open(sys.argv[1]))["said"]]' "$d/accounts.json"; echo '```'; } >> "${GITHUB_STEP_SUMMARY:-/dev/null}"
exit "$rc"
