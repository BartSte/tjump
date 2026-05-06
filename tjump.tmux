# vim: ft=tmux

bind -T copy-mode-vi h run-shell -b "$HOME/code/personal/tjump/bin/tjump --pane '#{pane_id}'"

