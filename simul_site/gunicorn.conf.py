import multiprocessing

bind = "0.0.0.0:8081"
workers = 2
threads = multiprocessing.cpu_count() * 2 + 1
max_requests = 1000
max_requests_jitter = 1000
worker_class = "uvicorn.workers.UvicornWorker"
wsgi_app = "simul_site.asgi:application"
