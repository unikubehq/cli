# Heavily inspired by the cleo project. Check it out.
# https://github.com/sdispater/cleo
# We use double curly braces to "escape" curly braces.
# Templates are rendered using Python's built-in `format` method for strings.


BASH_TEMPLATE = """{flag_complete_functions}
{function}()
{{
    local cur script coms opts com
    COMPREPLY=()
    _get_comp_words_by_ref -n : cur prev words
    # for an alias, get the real script behind it
    if [[ $(type -t ${{words[0]}}) == "alias" ]]; then
        script=$(alias ${{words[0]}} | sed -E "s/alias ${{words[0]}}='(.*)'/\\1/")
    else
        script=${{words[0]}}
    fi
    # lookup for command
    for word in ${{words[@]:1}}; do
        if [[ $word != -* ]]; then
            com=$word
            break
        fi
    done

    # completing for an option
    if [[ ${{cur}} == --* ]] ; then
        opts="{opts}"
        case "$com" in
{command_list}
        esac
        COMPREPLY=($(compgen -W "${{opts}}" -- ${{cur}}))
        __ltrim_colon_completions "$cur"
        return 0;
    fi

    if [[ $prev == $com ]]; then
        case "$com" in
            {subcommands}
        esac
    fi

    # completing for a command
    if [[ $cur == $com ]]; then
        coms="{coms}"
        COMPREPLY=($(compgen -W "${{coms}}" -- ${{cur}}))
        __ltrim_colon_completions "$cur"
        return 0
    fi
}}
{compdefs}"""

ZSH_TEMPLATE = """#compdef %(script_name)s
%(function)s()
{
    local state com cur
    cur=${words[${#words[@]}]}
    # lookup for command
    for word in ${words[@]:1}; do
        if [[ $word != -* ]]; then
            com=$word
            break
        fi
    done
    if [[ ${cur} == --* ]]; then
        state="option"
        opts=(%(opts)s)
    elif [[ $cur == $com ]]; then
        state="command"
        coms=(%(coms)s)
    fi
    case $state in
        (command)
            _describe 'command' coms
        ;;
        (option)
            case "$com" in
%(command_list)s
            esac
            _describe 'option' opts
        ;;
        *)
            # fallback to file completion
            _arguments '*:file:_files'
    esac
}
%(function)s "$@"
%(compdefs)s"""

FISH_TEMPLATE = """function __fish%(function)s_no_subcommand
    for i in (commandline -opc)
        if contains -- $i %(cmds_names)s
            return 1
        end
    end
    return 0
end
# global options
%(opts)s
# commands
%(cmds)s
# command options
%(cmds_opts)s"""


TEMPLATES = {"bash": BASH_TEMPLATE, "zsh": ZSH_TEMPLATE, "fish": FISH_TEMPLATE}
