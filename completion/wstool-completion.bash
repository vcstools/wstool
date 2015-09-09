# Software License Agreement (BSD License)
#
# Copyright (c) 2010, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# Programmable completion for the wstool command under bash. Source
# this file (or on some systems add it to ~/.bash_completion and start a new
# shell)

# ZSH support
if [[ -n ${ZSH_VERSION-} ]]; then
  autoload -U +X bashcompinit && bashcompinit
fi

# put here to be extendable
if [ -z "$WSTOOL_BASE_COMMANDS" ]; then
  _WSTOOL_BASE_COMMANDS="help init set merge info remove diff status update --version"
fi

# Based originally on the bzr/svn bash completition scripts.
_wstool_complete()
{
  local cur cmds cmdOpts opt helpCmds optBase i

  COMPREPLY=()
  cur=${COMP_WORDS[COMP_CWORD]}

  cmds=$_WSTOOL_BASE_COMMANDS

  if [[ $COMP_CWORD -eq 1 ]] ; then
    COMPREPLY=( $( compgen -W "$cmds" -- $cur ) )
    return 0
  fi

  # if not typing an option, or if the previous option required a
  # parameter, then fallback on ordinary filename expansion
  helpCmds='help|--help|h|\?'
  if [[ ${COMP_WORDS[1]} != @@($helpCmds) ]] && \
     [[ "$cur" != -* ]] ; then
    case ${COMP_WORDS[1]} in
    info|diff|di|status|st|remove|rm|update|up)
      cmdOpts=`wstool info --only=localname 2> /dev/null | sed 's,:, ,g'`
      COMPREPLY=( $( compgen -W "$cmdOpts" -- $cur ) )
    ;;
    set)
      if [[ $COMP_CWORD -eq 2 ]]; then
          cmdOpts=`wstool info --only=localname 2> /dev/null | sed 's,:, ,g'`
          COMPREPLY=( $( compgen -W "$cmdOpts" -- $cur ) )
      elif [[ $COMP_CWORD -eq 3 ]]; then
          cmdOpts=`wstool info ${COMP_WORDS[2]} --only=uri 2> /dev/null`
          COMPREPLY=( $( compgen -W "$cmdOpts" -- $cur ) )
      else
          if [[ ${COMP_WORDS[$(( $COMP_CWORD - 1 ))]} == "--version-new" ]]; then
              cmdOpts=`wstool info ${COMP_WORDS[2]} --only=version 2> /dev/null|sed 's/,$//'`
              COMPREPLY=( $( compgen -W "$cmdOpts" -- $cur ) )
          fi
      fi
    ;;
    esac
    return 0
  fi

  cmdOpts=
  case ${COMP_WORDS[1]} in
  status|st)
    cmdOpts="-t --target-workspace --untracked"
    ;;
  diff|di)
    cmdOpts="-t --target-workspace"
    ;;
  init)
    cmdOpts="-t --target-workspace --continue-on-error"
    ;;
  merge)
    cmdOpts="-t --target-workspace -y --confirm-all -r --merge-replace -k --merge-keep -a --merge-kill-append"
    ;;
  set)
    cmdOpts="-t --target-workspace --git --svn --bzr --hg --uri -v --version-new --detached -y --confirm"
    ;;
  remove|rm)
    cmdOpts="-t --target-workspace"
    ;;
  update|up)
    cmdOpts="-t --target-workspace  --delete-changed-uris --abort-changed-uris --backup-changed-uris"
    ;;
  snapshot)
    cmdOpts="-t --target-workspace"
    ;;
  info)
    cmdOpts="-t --target-workspace --data-only --no-pkg-path --pkg-path-only --only --yaml"
    ;;
  *)
    ;;
  esac

  cmdOpts="$cmdOpts --help -h"

  # take out options already given
  for (( i=2; i<=$COMP_CWORD-1; ++i )) ; do
    opt=${COMP_WORDS[$i]}

    case $opt in
    --*)    optBase=${opt/=*/} ;;
    -*)     optBase=${opt:0:2} ;;
    esac

    cmdOpts=" $cmdOpts "
    cmdOpts=${cmdOpts/ ${optBase} / }

    # take out alternatives
    case $optBase in
    -h)                 cmdOpts=${cmdOpts/ --help / } ;;
    --help)             cmdOpts=${cmdOpts/ -h / } ;;
    -t)                 cmdOpts=${cmdOpts/ --target-workspace / } ;;
    --target-workspace) cmdOpts=${cmdOpts/ -t / } ;;
    --delete-changed-uris)
      cmdOpts=${cmdOpts/ --abort-changed-uris / }
      cmdOpts=${cmdOpts/ --backup-changed-uris / }
    ;;
    --abort-changed-uris)
      cmdOpts=${cmdOpts/ --delete-changed-uris / }
      cmdOpts=${cmdOpts/ --backup-changed-uris / }
    ;;
    --backup-changed-uris)
      cmdOpts=${cmdOpts/ --delete-changed-uris / }
      cmdOpts=${cmdOpts/ --abort-changed-uris  / }
    ;;
    # scm options
    --svn)
      cmdOpts=${cmdOpts/ --git / }
      cmdOpts=${cmdOpts/ --hg / }
      cmdOpts=${cmdOpts/ --bzr / }
      cmdOpts=${cmdOpts/ --detached / }
    ;;
    --git)
      cmdOpts=${cmdOpts/ --svn / }
      cmdOpts=${cmdOpts/ --hg / }
      cmdOpts=${cmdOpts/ --bzr / }
      cmdOpts=${cmdOpts/ --detached / }
    ;;
    --hg)
      cmdOpts=${cmdOpts/ --git / }
      cmdOpts=${cmdOpts/ --svn / }
      cmdOpts=${cmdOpts/ --bzr / }
      cmdOpts=${cmdOpts/ --detached / }
    ;;
    --bzr)
      cmdOpts=${cmdOpts/ --git / }
      cmdOpts=${cmdOpts/ --hg / }
      cmdOpts=${cmdOpts/ --svn / }
      cmdOpts=${cmdOpts/ --detached / }
    ;;
    --detached)
      cmdOpts=${cmdOpts/ --git / }
      cmdOpts=${cmdOpts/ --hg / }
      cmdOpts=${cmdOpts/ --bzr / }
      cmdOpts=${cmdOpts/ --svn / }
    ;;
    # merge options
    --merge-replace)
      cmdOpts=${cmdOpts/ --merge-keep / }
      cmdOpts=${cmdOpts/ --merge-kill-append / }
      cmdOpts=${cmdOpts/ -r / }
      cmdOpts=${cmdOpts/ -a / }
      cmdOpts=${cmdOpts/ -k / }
    ;;
    --merge-keep)
      cmdOpts=${cmdOpts/ --merge-replace / }
      cmdOpts=${cmdOpts/ --merge-kill-append / }
      cmdOpts=${cmdOpts/ -r / }
      cmdOpts=${cmdOpts/ -a / }
      cmdOpts=${cmdOpts/ -k / }
    ;;
    --merge-kill-append)
      cmdOpts=${cmdOpts/ --merge-keep / }
      cmdOpts=${cmdOpts/ --merge-replace / }
      cmdOpts=${cmdOpts/ -r / }
      cmdOpts=${cmdOpts/ -a / }
      cmdOpts=${cmdOpts/ -k / }
    ;;
    -r)
      cmdOpts=${cmdOpts/ --merge-keep / }
      cmdOpts=${cmdOpts/ --merge-kill-append / }
      cmdOpts=${cmdOpts/ --merge-replace / }
      cmdOpts=${cmdOpts/ -a / }
      cmdOpts=${cmdOpts/ -k / }
    ;;
    -a)
      cmdOpts=${cmdOpts/ --merge-keep / }
      cmdOpts=${cmdOpts/ --merge-kill-append / }
      cmdOpts=${cmdOpts/ --merge-replace / }
      cmdOpts=${cmdOpts/ -r / }
      cmdOpts=${cmdOpts/ -k / }
    ;;
    -k)
      cmdOpts=${cmdOpts/ --merge-keep / }
      cmdOpts=${cmdOpts/ --merge-kill-append / }
      cmdOpts=${cmdOpts/ --merge-replace / }
      cmdOpts=${cmdOpts/ -a / }
      cmdOpts=${cmdOpts/ -r / }
    ;;
    esac

    # skip next option if this one requires a parameter
    if [[ $opt == @@($optsParam) ]] ; then
      ((++i))
    fi
  done

  COMPREPLY=( $( compgen -W "$cmdOpts" -- $cur ) )

  return 0

}
complete -F _wstool_complete -o default wstool
