import time
from tqdm import tqdm

while True:
    print("Введи количество ms*100: ")
    t = input()
    for i in tqdm(range(int(t))):
        t = (i+123423423428*333)/83746983763984756

    print("Введи количество ms*100 ERROR: ")
    t = input()
    for i in tqdm(range(t)):
        time.sleep(100)