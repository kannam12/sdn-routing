## Quick start

1a) Uruchamianie podstawowej topologii minineta:

`sudo mn --controller=remote,ip=127.0.0.1,port=5555`

`sudo python3 polska-z-ruchem.py` już też zadziała

1b) Uruchamianie customowej topologii:

`jeszcze nic`

2\) Uruchamianie sterownika:

`ryu-manager --ofp-tcp-listen-port 5555 --verbose skrypcik.py --observe-links` 

`--observe-links` jest potrzebne do automatycznego wykrywania topologi

## Opis działania
