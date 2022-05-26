#!/usr/bin/env bash
function log {
  printf "\033[94m%s\033[0m\n" "$1"
}
log "Synchronising with remote repository..."
git pull origin master
log "Installing dependencies..."
/usr/bin/env python3 -m pip install -r requirements.txt
log "Moving files..."
function copy_files {
  for filename in "$1"/*
  do
    sub_files="$(ls "$filename")"
    new_file=${filename#"templates/"}
    if [ "$sub_files" != "$filename" ]
    then
      mkdir "$new_file" 2> /dev/null
      if [ "$sub_files" != "" ]
      then
        copy_files "$filename"
      fi
    else
      if ! (cat "$new_file" &> /dev/null)
      then
        cp "$filename" "$new_file"
      fi
    fi

  done
}
copy_files "templates"
if [ "$1" != "dev" ]
then
  rm -rf templates
fi
log "Setup complete"