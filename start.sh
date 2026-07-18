#!/bin/bash

if [ -z "$UPSTREAM_REPO" ]
then
  echo "Cloning main Repository"
  git clone https://github.com/svnig7/Filter-Bot.git /EvaMaria
else
  echo "Cloning Custom Repo from $UPSTREAM_REPO"
  git clone "$UPSTREAM_REPO" /EvaMaria
fi

cd /EvaMaria || exit 1

pip3 install -U -r requirements.txt

echo "Starting Bot...."
exec python3 bot.py
