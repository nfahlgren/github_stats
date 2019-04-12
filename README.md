# Collect traffic statistics for a GitHub repository

## Problem

GitHub tracks traffic statistics for repositories under "Insights" > "Traffic" but the statistics that are available
through GitHub only cover the past 12 days.

## Purpose

The simple script in this repository, run on a daily schedule, will log the number of total and unique clones and views 
for any of your GitHub repositories that you want to track.

## Setup

### Generate a GitHub access token

You will need a GitHub access token to use the GitHub API. 

1. Log into GitHub.
2. Navigate to the Personal access tokens page (Settings > Developer settings > Personal access tokens), 
or just go [here](https://github.com/settings/tokens).
3. If you do not already have a token or need a new one, select Generate new token.
4. Unless you need access to private repositories or other advanced features, the easiest thing to do is check the box
"public_repo", which gives you "Access public repositories".
5. After you create the token you will need to copy the token key value. If you ever forget the token you will have to
regenerate it.

### Create a configuration file for your repository

An example configuration file is provided. Make a copy of the example file and edit the three values.

* "db" is the path/name of the SQLite database file that will store your statistics.
* "repo" is the name of the username/organization and repository in the form "username/repository".
* "access_token" is the token key you created above.

### Run the script to test it

The Python script accepts the configuration file as the only input. If the specified database does not exist it will
automatically create it and build the two tables.

```bash
python github-stats.py --config repo.config.json
```

If this is successful, you should have a new SQLite database file with up to 12 days of clones and views statistics.
You can export the data to CSV using the following commands:

```bash
sqlite3 -header -csv repo.db.sqlite3 "select * from clones" > repo.clones.csv
sqlite3 -header -csv repo.db.sqlite3 "select * from views" > repo.views.csv
```

### Gathering statistics on a schedule

The script will add any new daily traffic records to the database whenever it is run. In principle, as long as you run
the script once every 12 days you should be able to collect daily traffic statistics. I run the script once per day
using the cron scheduler in Linux. For example, open the crontab file for your user account:

```bash
crontab -e
```

Here is an example cron task that runs `github-stats.py` daily at 4am.

```
# Example of job definition:
# .---------------- minute (0 - 59)
# |  .------------- hour (0 - 23)
# |  |  .---------- day of month (1 - 31)
# |  |  |  .------- month (1 - 12) OR jan,feb,mar,apr ...
# |  |  |  |  .---- day of week (0 - 6) (Sunday=0 or 7) OR sun,mon,tue,wed,thu,fri,sat
# |  |  |  |  |
# *  *  *  *  * command to be executed
0 4 * * * python /home/user/github_stats/github-stats.py --config /home/user/repo.config
```

If you want to track multiple repositories just add additional cron tasks for each one.
