import time

while True:
    t = time.time()
    time.sleep(1)
    print('Sleeping... ' + str(time.time() - t)[0:10] )
