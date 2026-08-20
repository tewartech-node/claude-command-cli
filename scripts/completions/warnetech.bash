#!/usr/bin/env bash
# Bash tab-completion for the four Warnetech console scripts:
# warnetech, warnetech-curriculum, warnetech-backup-recall, warnetech-doctor.
#
# Install: source it from ~/.bashrc, or let
# scripts/install-curriculum-hook.sh / bootstrap_termux.sh do it for you.
#
#   echo 'source ~/claude-command-cli/scripts/completions/warnetech.bash' >> ~/.bashrc
#
# zsh users: `autoload -Uz bashcompinit && bashcompinit` in ~/.zshrc, then
# source this same file -- one completion implementation, not two to keep
# in sync.
#
# The subcommand lists below are the maintenance surface: each is one
# space-separated variable, matched 1:1 against each tool's real argparse
# subcommands by tests/cli/test_completion.py, which fails the build the
# moment a subcommand is added or renamed here and not there (or vice
# versa). Edit the variable, not the function, when a CLI's commands change.

_WARNETECH_CLI_SUBCOMMANDS="status metrics signatures learn recover slice compress ghost-create ghost-recall retention-apply retention-policy ai-query ai-recall export import config server-ping db-check db-sync ai-diagnose"

_WARNETECH_CURRICULUM_SUBCOMMANDS="check preflight learn resolve log verify curriculum seed packages"

_WARNETECH_BACKUP_RECALL_SUBCOMMANDS="backup list verify recall push-s3 pull-s3"

_WARNETECH_DOCTOR_FLAGS="--json --root"

_warnetech_complete_first_word() {
    # All four tools take their subcommand (or, for doctor, a flag) as the
    # first word; nothing here attempts to complete flags or arguments
    # *within* a subcommand, since those change per-tool and per-release
    # far more often than the subcommand names themselves do.
    local cur words
    cur="${COMP_WORDS[COMP_CWORD]}"
    words="$1"
    if [ "$COMP_CWORD" -eq 1 ]; then
        COMPREPLY=( $(compgen -W "$words" -- "$cur") )
    fi
}

_warnetech_complete() { _warnetech_complete_first_word "$_WARNETECH_CLI_SUBCOMMANDS"; }
_warnetech_curriculum_complete() { _warnetech_complete_first_word "$_WARNETECH_CURRICULUM_SUBCOMMANDS"; }
_warnetech_backup_recall_complete() { _warnetech_complete_first_word "$_WARNETECH_BACKUP_RECALL_SUBCOMMANDS"; }
_warnetech_doctor_complete() { _warnetech_complete_first_word "$_WARNETECH_DOCTOR_FLAGS"; }

complete -F _warnetech_complete warnetech
complete -F _warnetech_curriculum_complete warnetech-curriculum
complete -F _warnetech_backup_recall_complete warnetech-backup-recall
complete -F _warnetech_doctor_complete warnetech-doctor
