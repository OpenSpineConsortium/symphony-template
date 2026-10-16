#!/bin/bash
# The grid's two tool tests, the runner's and the CI lane's, under the login node's own stack:
# CentOS 7 with bash 4.2.46 and Python 3.6, jq from EPEL, as they ran on 2026-10-16 for the
# runner's review (wsu-grid-and-github-actions.md beside this file, "How the fixes were proven").
# hpcworker's CI runs neither on bash 4.2: its centos 7 job runs the framework suite alone, and the
# runner's tests run in CI only once the owner adds their step. Run it inside a centos:7 container
# with an hpcworker checkout at /src, read-only; it copies the checkout before running anything:
#
#   docker run --rm --network host -e HTTPS_PROXY -e HTTP_PROXY -e https_proxy -e http_proxy \
#     -e NO_PROXY -e no_proxy -v /root/.ccr/ca-bundle.crt:/ccr-ca.crt:ro \
#     -v <hpcworker checkout>:/src:ro -v <this file>:/run-tests.sh:ro centos:7 bash /run-tests.sh
#
# The proxy's variables and its CA bundle at /ccr-ca.crt are what a Claude Code cloud session needs
# for yum to reach vault.centos.org; elsewhere they are left out. Each test prints its failures and
# its exit status; "exit 0" twice is a pass.
set -uo pipefail
cp /ccr-ca.crt /etc/pki/ca-trust/source/anchors/ccr.crt 2>/dev/null && update-ca-trust extract >/dev/null 2>&1
sed -i -e 's|^mirrorlist=|#mirrorlist=|' -e 's|^#baseurl=http://mirror.centos.org|baseurl=http://vault.centos.org|' /etc/yum.repos.d/CentOS-*.repo
yum install -q -y python3 epel-release > /tmp/yum1.log 2>&1 || { echo "yum install python3 failed"; tail -5 /tmp/yum1.log; exit 1; }
yum install -q -y jq > /tmp/yum2.log 2>&1 || { echo "yum install jq failed"; tail -5 /tmp/yum2.log; exit 1; }
bash --version | head -1; python3 --version; jq --version
cp -a /src /home/src && cd /home/src || exit 1
echo "== test_grid_runner.sh"; bash tools/tests/test_grid_runner.sh 2>&1 | grep -v '^ok'; echo "exit ${PIPESTATUS[0]}"
echo "== test_grid_ci.sh"; bash tools/tests/test_grid_ci.sh 2>&1 | grep -v '^ok'; echo "exit ${PIPESTATUS[0]}"
