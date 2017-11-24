#!/bin/bash
# root/start.sh
#
# run:
#   $ . start.sh <args>
#
function clean_env() {
    unset APP_CONFIG
    unset FLASK_DEBUG
    unset FLASK_APP

    unset BOKEH_LOG_LEVEL
    unset BOKEH_PY_LOG_LEVEL

    unset APP_DB_USERNAME
    unset APP_DB_PASSWORD
    unset APP_DB_NAME

    unset APP_MAIL_USERNAME
    unset APP_MAIL_PASSWORD

    unset APP_ADM_FIRSTNAME
    unset APP_ADM_LASTNAME
    unset APP_ADM_USERNAME
    unset APP_ADM_PASSWORD
    unset APP_ADM_MAIL
}

function init_env_vars() {
    export FLASK_APP="app/__init__.py"

    export APP_CONFIG="config.DevelopmentConfig"
    export FLASK_DEBUG=1
    export BOKEH_LOG_LEVEL=info         # browser-side log: info/debug
    export BOKEH_PY_LOG_LEVEL=debug     # server-side log:  none/debug
    source instance/my_env_vars.sh

    # export APP_CONFIG="config.ProductionConfig"
    # export BOKEH_LOG_LEVEL=info
    # export BOKEH_PY_LOG_LEVEL=none
}

this_script=${BASH_SOURCE[0]}

if [[ -n $1 ]]; then
    case $1 in
        -h | --help)
            echo "help functionality not implemented"
            ;;
        --clean-db)
            init_env_vars
            echo "Dropping db and migration files and clear env vars..."

            python manage.py drop_db
            rm -rf migrations
            clean_env
            ;;
        --create-db)
            init_env_vars
            echo "Creating db, migration files and db admin user..."

            python manage.py create_db
            python manage.py db init
            python manage.py db migrate
            python manage.py create_admin
            ;;
        --upgrade-db)
            init_env_vars
            echo "Upgrading db with flask migrations..."

            # if "migrations" dir doesn't exists, create it
            if [[ ! -d $PWD"/migrations" ]]; then
                python manage.py db init
            fi
            python manage.py db migrate
            python manage.py db upgrade
            ;;
        --upgrade-flask)
            source $this_script --upgrade-db
            source $this_script --flask-app
            ;;
        --upgrade-full)
            source $this_script --upgrade-db
            source $this_script --full-app
            ;;
        --reset-db)
            echo "Resetting db..."
            source $this_script --clean-db
            source $this_script --create-db
            ;;
        --reset-flask)
            source $this_script --reset-db
            source $this_script --flask-app
            ;;
        --reset-full)
            source $this_script --reset-db
            source $this_script --full-app
            ;;
        -f | --flask-app)
            echo "Minor start: just Flask application"
            init_env_vars

            flask run --host localhost --port 5000
            ;;
        -b | --bokeh-app)
            echo "Minor start: just Bokeh application"
            init_env_vars

            python app/_bokeh/_bokeh.py
            ;;
        -a | --full-app)
            echo "Default start: Flask and Bokeh applications"
            init_env_vars

            python app/_bokeh/_bokeh.py &
            flask run --host localhost --port 5000
            ;;
        -t | --test)
            # To make dev tests
            if [[ ! -d $PWD"/migration" ]]; then
                echo "no dir"
            else
                echo "exists"
            fi
            ;;
        *)
            echo "There is no command: $1"
            ;;
    esac
else
    echo 'Invalid argument provided. Try help section for more information:'
    echo '$ . start.sh --help'
fi
