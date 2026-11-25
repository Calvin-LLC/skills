#!/usr/bin/env sh
set -eu

REPO_SLUG="Calvin-LLC/skills"
REPO_URL="https://github.com/${REPO_SLUG}.git"

SOURCE=""
STASH=0
while [ $# -gt 0 ]; do
  case "$1" in
    --source)
      [ $# -ge 2 ] || { echo "--source needs a path" >&2; exit 2; }
      SOURCE="$2"; shift 2 ;;
    --stash) STASH=1; shift ;;
    *) echo "Usage: install.sh [--source <checkout>] [--stash]" >&2; exit 2 ;;
  esac
done

# SKILLS_HOME points the whole install at another directory (tests).
if [ -n "${SKILLS_HOME:-}" ]; then
  USER_HOME="${SKILLS_HOME}"
  CLAUDE_ROOT="${USER_HOME}/.claude"
  MUSE_ROOT="${USER_HOME}/.config/muse"
  CODEX_ROOT="${USER_HOME}/.codex"
else
  USER_HOME="${HOME}"
  CLAUDE_ROOT="${CLAUDE_CONFIG_DIR:-${HOME}/.claude}"
  MUSE_ROOT="${MUSE_CONFIG_DIR:-${HOME}/.config/muse}"
  CODEX_ROOT="${CODEX_HOME:-${HOME}/.codex}"
fi
DEST="${USER_HOME}/.agents/calvin-skills"

if [ -n "${SOURCE}" ]; then
  SOURCE="$(cd "${SOURCE}" && pwd)"
  git -C "${SOURCE}" rev-parse --verify --quiet refs/heads/main >/dev/null ||
    { echo "Source ${SOURCE} is not a git checkout with a main branch." >&2; exit 1; }
fi

mkdir -p "${USER_HOME}/.agents/skills"

if [ -d "${DEST}/.git" ]; then
  if [ -n "${SOURCE}" ]; then
    dirty="$(git -C "${DEST}" status --porcelain | wc -l | tr -d ' ')"
    if [ "${dirty}" -gt 0 ] && [ "${STASH}" = 1 ]; then
      identity=""
      git -C "${DEST}" config user.name >/dev/null 2>&1 || identity="-c user.name=calvin-skills -c user.email=calvin-skills@localhost"
      # shellcheck disable=SC2086
      git ${identity} -C "${DEST}" stash push --include-untracked -m "calvin-skills install $(date -u '+%Y-%m-%d %H:%M:%S') UTC"
      echo "Stashed ${dirty} uncommitted paths from ${DEST}. Restore with: git -C \"${DEST}\" stash list"
    elif [ "${dirty}" -gt 0 ]; then
      {
        echo "Refusing to update ${DEST}. It has ${dirty} uncommitted paths, so it no longer matches any commit."
        echo "Rerun with --stash to set them aside in a git stash, which deletes nothing:"
        echo "  sh \"$0\" --source \"${SOURCE}\" --stash"
      } >&2
      exit 1
    fi
    echo "Updating ${DEST} from ${SOURCE}..."
    git -C "${DEST}" fetch --quiet "${SOURCE}" main
    if ! git -C "${DEST}" merge-base --is-ancestor HEAD FETCH_HEAD; then
      old="$(git -C "${DEST}" rev-parse --short HEAD)"
      echo "Clone was at ${old}, which the source's main no longer contains (amended or rebased). Moving it; ${old} stays in the clone's reflog."
    fi
    # The tree is clean here, and --keep refuses to move over a local change.
    git -C "${DEST}" reset --quiet --keep FETCH_HEAD
  else
    echo "Updating ${REPO_SLUG} in ${DEST}..."
    git -C "${DEST}" pull --ff-only
  fi
else
  rm -rf "${DEST}"
  if [ -n "${SOURCE}" ]; then
    echo "Cloning ${SOURCE} to ${DEST}..."
    git clone --branch main "${SOURCE}" "${DEST}"
    git -C "${DEST}" remote set-url origin "${REPO_URL}"
  else
    echo "Cloning ${REPO_SLUG} to ${DEST}..."
    if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
      gh repo clone "${REPO_SLUG}" "${DEST}" -- --depth 1
    else
      git clone --depth 1 "${REPO_URL}" "${DEST}"
    fi
  fi
fi

if [ -n "${SOURCE}" ]; then
  git -C "${SOURCE}" config core.hooksPath scripts/hooks
fi

muse_cmd=""
if command -v muse >/dev/null 2>&1; then
  muse_cmd="$(command -v muse)"
  # A test home must never reach the real Muse, so only a muse stub inside it counts.
  if [ -n "${SKILLS_HOME:-}" ]; then
    case "${muse_cmd}" in "${USER_HOME}"/*) ;; *) muse_cmd="" ;; esac
  fi
fi
[ -d "${MUSE_ROOT}" ] || muse_cmd=""
muse_managed=0
[ -d "${MUSE_ROOT}/skills/.muse" ] && muse_managed=1

# 1. Symlink Skills into all agent roots
for target_root in \
  "${USER_HOME}/.agents/skills" \
  "${CLAUDE_ROOT}/skills" \
  "${USER_HOME}/.hermes/skills" \
  "${MUSE_ROOT}/skills" \
  "${CODEX_ROOT}/skills"
do
  if [ "${muse_managed}" = 1 ] && [ "${target_root}" = "${MUSE_ROOT}/skills" ]; then
    echo "Muse Code manages its own copies -> ${target_root}"
    continue
  fi
  if [ ! -d "$(dirname "${target_root}")" ]; then
    echo "Skipped ${target_root}. Its harness is not installed (no $(dirname "${target_root}"))"
    continue
  fi
  mkdir -p "${target_root}"
  for skill_dir in "${DEST}"/skills/*; do
    [ -d "${skill_dir}" ] || continue
    [ -f "${skill_dir}/SKILL.md" ] || continue
    skill_name="$(basename "${skill_dir}")"
    link="${target_root}/${skill_name}"
    if [ -d "${link}" ] && [ ! -L "${link}" ]; then rm -rf "${link}"; fi
    ln -sfn "${skill_dir}" "${link}"
  done
  for entry in "${target_root}"/*; do
    [ -L "${entry}" ] && [ ! -e "${entry}" ] || continue
    case "$(readlink "${entry}")" in "${DEST}/skills/"*) rm -f "${entry}" ;; esac
  done
  echo "Linked all skills -> ${target_root}"
done

for extra in "${USER_HOME}/.omp/agent/skills" "${USER_HOME}/.pi/agent/skills"; do
  for entry in "${extra}"/*; do
    [ -L "${entry}" ] || continue
    case "$(readlink "${entry}")" in "${DEST}/skills/"*) rm -f "${entry}" ;; esac
  done
  rmdir "${extra}" 2>/dev/null || true
done
echo "OMP loads skills from its plugin: omp plugin install github:Calvin-LLC/skills, then omp plugin upgrade @calvin-llc/skills after each push"
echo "Pi loads skills from ${USER_HOME}/.agents/skills"

# Muse Code copies skills into its own folder and tracks them in .muse; only muse may change that folder.
if [ -n "${muse_cmd}" ]; then
  if [ "${muse_managed}" = 1 ]; then
    for skill_dir in "${DEST}"/skills/*; do
      [ -f "${skill_dir}/SKILL.md" ] || continue
      skill_name="$(basename "${skill_dir}")"
      if [ -e "${MUSE_ROOT}/skills/${skill_name}" ] && grep -F -q "${DEST}/skills/${skill_name}\"" "${MUSE_ROOT}/skills/.muse/lock.json" 2>/dev/null; then
        set -- skills update "${skill_name}"
      elif [ -e "${MUSE_ROOT}/skills/${skill_name}" ]; then
        set -- skills install "${skill_dir}" --scope user --force
      else
        set -- skills install "${skill_dir}" --scope user
      fi
      "${muse_cmd}" "$@" >/dev/null 2>&1 || echo "warning: muse $* failed" >&2
    done
    for entry in "${MUSE_ROOT}/skills"/*; do
      [ -d "${entry}" ] || continue
      skill_name="$(basename "${entry}")"
      [ -d "${DEST}/skills/${skill_name}" ] && continue
      grep -F -q "${DEST}/skills/${skill_name}\"" "${MUSE_ROOT}/skills/.muse/lock.json" 2>/dev/null || continue
      "${muse_cmd}" skills uninstall "${skill_name}" >/dev/null 2>&1 || echo "warning: muse skills uninstall ${skill_name} failed" >&2
    done
    echo "Updated Muse Code skills with muse"
  fi
  for skill_dir in "${DEST}"/skills/*; do
    [ -f "${skill_dir}/SKILL.md" ] || continue
    "${muse_cmd}" skills enable "$(basename "${skill_dir}")" --scope user >/dev/null 2>&1 || true
  done
  echo "Enabled all skills in Muse Code"
elif [ "${muse_managed}" = 1 ]; then
  echo "Muse Code skills in ${MUSE_ROOT}/skills are managed by muse and muse is not on PATH. Left unchanged. Run this installer again where muse is available."
fi

# 2. Symlink SOUL.md into each harness under the name it loads. OMP reads RULES.md, in main
# sessions and subagents, and Muse Code reads AGENTS.md. Neither reads SOUL.md.
if [ -f "${DEST}/SOUL.md" ]; then
  for soul_link in \
    "${USER_HOME}/.pi/agent/SOUL.md" \
    "${USER_HOME}/.hermes/SOUL.md" \
    "${USER_HOME}/.agents/SOUL.md" \
    "${USER_HOME}/.omp/agent/RULES.md" \
    "${MUSE_ROOT}/AGENTS.md"
  do
    [ -d "$(dirname "${soul_link}")" ] || continue
    ln -sfn "${DEST}/SOUL.md" "${soul_link}"
    echo "Linked SOUL.md -> ${soul_link}"
  done
fi

omp_rules="${USER_HOME}/.omp/agent/rules"
if [ -d "${USER_HOME}/.omp/agent" ]; then
  mkdir -p "${omp_rules}"
  for rule in "${DEST}"/rules/*.md; do
    [ -f "${rule}" ] || continue
    ln -sfn "${rule}" "${omp_rules}/$(basename "${rule}")"
  done
  for entry in "${omp_rules}"/*; do
    [ -L "${entry}" ] && [ ! -e "${entry}" ] || continue
    case "$(readlink "${entry}")" in "${DEST}/rules/"*) rm -f "${entry}" ;; esac
  done
  echo "Linked OMP rules -> ${omp_rules}"
fi

echo ""
echo "Installed skills:"
count=0
for skill_dir in "${DEST}"/skills/*; do
  [ -f "${skill_dir}/SKILL.md" ] || continue
  s="$(basename "${skill_dir}")"
  count=$((count + 1))
  echo "  - ${s}  (Claude Code/Hermes/Muse Code: /${s} | OMP/Pi: /skill:${s} | Codex: \$${s})"
done
echo "Synced calvin-skills at $(git -C "${DEST}" rev-parse --short HEAD) (${count} skills) -> ${DEST}"
