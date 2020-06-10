import multiprocessing as mp

bind = '0.0.0.0:80'

workers = mp.cpu_count() * 2 - 1

worker_class = 'gevent'

# threads = 2
