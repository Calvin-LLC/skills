#!/usr/bin/env sh
set -eu

REPO_SLUG="Calvin-LLC/skills"
REPO_URL="https://github.com/${REPO_SLUG}.git"
DEST="${HOME}/.agents/calvin-skills"

mkdir -p "${HOME}/.agents/skills"

if [ -d "${DEST}/.git" ]; then
  echo "Updating ${REPO_SLUG} in ${DEST}..."
  git -C "${DEST}" pull --ff-only
else
  rm -rf "${DEST}"
  echo "Cloning ${REPO_SLUG} to ${DEST}..."
  if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then
    gh repo clone "${REPO_SLUG}" "${DEST}" -- --depth 1
  else
    git clone --depth 1 "${REPO_URL}" "${DEST}"
  fi
fi

# 1. Symlink Skills into all agent roots
for target_root in \
  "${HOME}/.agents/skills" \
  "${CLAUDE_CONFIG_DIR:-${HOME}/.claude}/skills" \
  "${HOME}/.pi/agent/skills" \
  "${HOME}/.omp/agent/skills" \
  "${HOME}/.hermes/skills"
do
  mkdir -p "${target_root}"
  for skill_dir in "${DEST}"/skills/*; do
    [ -d "${skill_dir}" ] || continue
    [ -f "${skill_dir}/SKILL.md" ] || continue
    skill_name="$(basename "${skill_dir}")"
    ln -sfn "${skill_dir}" "${target_root}/${skill_name}"
  done
  echo "Linked all skills -> ${target_root}"
done

# 2. Symlink SOUL.md into agent identity roots where supported (Pi, Hermes, OMP, Claude)
if [ -f "${DEST}/SOUL.md" ]; then
  for soul_root in \
    "${HOME}/.pi/agent" \
    "${HOME}/.hermes" \
    "${HOME}/.omp/agent" \
    "${HOME}/.agents"
  do
    mkdir -p "${soul_root}"
    ln -sfn "${DEST}/SOUL.md" "${soul_root}/SOUL.md"
    echo "Linked SOUL.md -> ${soul_root}/SOUL.md"
  done
fi

echo ""
echo "Installed skills:"
for skill_dir in "${DEST}"/skills/*; do
  [ -f "${skill_dir}/SKILL.md" ] || continue
  s="$(basename "${skill_dir}")"
  echo "  - ${s}  (Claude/Hermes: /${s} | Pi/OMP: /skill:${s})"
done
