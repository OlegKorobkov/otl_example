# otl_example
в manage.py автоподключение инструментов на весь проект

автоподключение celery
для работы трекинга инструмент должен быть включен как на клиенте(в django приложении в manage.py) так и на воркере celery
в https://github.com/OlegKorobkov/otl_example/blob/master/hackernews/celery.py

создание спанов через декоратор/with
и работа со спаном: добавление атрибутов и логов к спану
https://github.com/OlegKorobkov/otl_example/blob/master/links/schema.py#L91

Для автотрейсинга psycopg2-binary необходимо подключать с параметром skip_dep_check=True, иначе Psycopg2Instrumentor думает, что psycopg2 не установлен

Psycopg2Instrumentor().instrument(skip_dep_check=True)
