# API for Mieux Voter

This API allows you to create elections, vote and obtain results with [majority judgment](https://en.wikipedia.org/wiki/Majority_judgment).

You can use our server at [demo.mieuxvoter.fr/api/](demo.mieuxvoter.fr/api/).

## Table of contentes
1. [Installation with Docker](#installation-with-docker)
    - [Configuration](#configuration)
        - [SMTP server configuration](#smtp-server-configuration)
            - [Gmail](#gmail)
            - [MailGun](#mailgun)
    - [Fist launch](#first-launch)
2. [Browse the admin](#browse-the-admin)
3. [Run the tests](#run-the-tests)
4. [Create databases migrations](#create-databases-migrations)



## Installation with Docker

### Configuration

Edit the `.env` with your own settings. A secret key can be generated in Python REPL:

```
>>> from django.core.management.utils import get_random_secret_key
>>> get_random_secret_key()
```

#### SMTP server configuration

##### Gmail

If you want to use Gmail to send emails, create a `.env.local` with :

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_PORT=587
EMAIL_HOST_USER= address of a gmail account
EMAIL_HOST_PASSWORD=gmail account password
```

For the gmail account, it is better to create one specially for this.
In "Manage your google account" / "security" activated the option "Less secure access of applications"

##### Mailgun

If you want to use MailGun to send emails, create a `.env.local` with :

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.mailgun.org
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_PORT=587
EMAIL_HOST_USER= Username provided by Mailgun
EMAIL_HOST_PASSWORD= Password provided by Mailgun
```
### First launch

Launch the dockers with:

```
sudo docker-compose up --build
```

Next in another terminal apply databases migrations with:

```
sudo docker/migrate.sh
```

Then create and apply the traduction with :

```
sudo docker exec -it mvapi_web_1 django-admin makemessages -a
sudo docker exec -it mvapi_web_1 django-admin compilemessages
```
You can now stop the dockers with : `Crtl + C` 

Finally launch the docker with :

```
sudo docker-compose up -d
```

## Browse the admin

Create a super-user:

```
sudo docker exec -it mvapi_web_1 python ./manage.py createsuperuser
```

Visit the admin page at [http://localhost:8012/admin/](http://localhost:8012/admin/).

## Run the tests

`sudo docker/test.sh`

## Create databases migrations

`sudo docker/makemigrations.sh`
