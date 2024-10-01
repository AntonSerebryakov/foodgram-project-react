## Проект Foodgram

Foodgram - дипломный проект, который представляет из себя продуктовый помощник с базой кулинарных рецептов. Публикуйте рецепты, подписывайтесь на других авторов, добавляйте продукты из рецептов в список покупок. 

### Технологии:

Python, Django, Django Rest Framework, Docker, NGINX, PostgreSQL, GitHubActions

### Развернуть проект на удаленном сервере:

- Клонировать репозиторий:
```
https://github.com/AntonSerebryakov/foodgram-project-react
```

- На сервере установите Docker и Docker Compose:

```
Необходимые пакеты:

sudo apt-get install \
    ca-certificates \
    curl \
    gnupg \
    lsb-release

Добавьте официальный GPG-ключ Docker:

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

Добавьте репозиторий Docker:

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

Обновите список пакетов еще раз:

sudo apt-get update

Установите Docker Engine:

sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin


```

- Скопировать на сервер файлы docker-compose.yml

```

```

- Скопировать на сервер файл .env c переменными окружения:
```
Пример файла .env
POSTGRES_USER=django_user              #пользователь бд
POSTGRES_PASSWORD=mysecretpassword     #пароль бд
POSTGRES_DB=django                     #база данных
DB_HOST=db                             #хост бд
DB_PORT=5432                           #порт бд
DJANGO_DEBUG = False                   #включен ли Debug
DJANGO_SECRET_KEY = django-insecure-cg6*%6d51ef8f#4!r3*$vmxm4) abgjw8mo!4y-q*uq1!4$-89$               #секретный ключ Django
ALLOWED_HOSTS=10.10.10.10,127.0.0.1,localhost,ваш_адрес.org   #разрешенные хосты
DJANGO_SUPERUSER_USERNAME=admin        #логин суперпользователя сайта
DJANGO_SUPERUSER_EMAIL=email@mail.ru   #email суперпользователя
DJANGO_SUPERUSER_PASSWORD=password     #пароль суперпользователя  
DJANGO_SUPERUSER_FIRST_NAME=Ivan       #имя суперпользователя
DJANGO_SUPERUSER_LAST_NAME=Ivanov      #Фамилия суперпользователя

```

```
- Перейдите в папку с файлом .env

cd foodgram

```

- Создать и запустить контейнеры Docker
```
sudo docker compose -f docker-compose.production.yml pull
sudo docker compose -f docker-compose.production.yml down
sudo docker compose -f docker-compose.production.yml up -d
```

- После сборки выполните миграции:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
```

- Создадим суперпользователя:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py create_superuser
```

- Соберем статику:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic --no-input
```

- Наполним базу данных базовыми ингредиентами из файла ingredients.json:
```
sudo docker compose -f docker-compose.production.yml exec backend python manage.py import_ingredients
```
