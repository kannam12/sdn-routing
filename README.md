## Quick start

### Uruchamianie przygotowanej topologii Polska w środowisku Mininet:

`sudo python3 setup-topo-generate-traffic.py --topo=fixed` 

Powyższy skrypt:
1. **Zestawia sieć**.
> W przypadku chęci skorzystania z dowolnej innej topologii zapisanej w formacie .gml należy użyć `--topo=from-gml` oraz zapisać plik .gml w tym samym folderze pod nazwą *custom-topo.gml*.

> Istnieje również testowa wariacja `--topo=fixed-no-loops`.

> W przypadku chęci skorzystania z topologii proponowanej przez mininet, np. tree należy do standardowej komendy dodać `--controller=remote,ip=127.0.0.1,port=5555`
2. Na każdym z hostów **uruchamia serwer Iperf oraz inicjuje testowe przepływy**. Wyniki dla poszczególnych hostów zapisywane są w *results/results_<host_IP>.txt*


### Uruchamianie sterownika i zaimplementowanej funckjonalności:

`ryu-manager --ofp-tcp-listen-port 5555 --verbose routing.py --observe-links` 

* `--observe-links` jest potrzebne do automatycznego wykrywania topologii
* można pominąć opcję `--verbose`
* uruchamianie razem z GUI:

`ryu-manager --ofp-tcp-listen-port 5555  --observe-links ryu/ryu/app/gui_topology/gui_topology.py sdn-routing/routing.py`


## Opis działania skryptu *routing.py*

1. Co kilka sekund wysyłamy requesta o statystyki portów.
1. Z uzyskanych danych wybieramy informację o aktualnej zajętości sieci, czyli konkretnie ile bajtów zostało przesłane przez dany interfejs (każde łącze w każdym kierunku).
1. Liczymy średnią zajętość podczas ostatniego okresu obserwacji (dla każdego łącza w każdym kierunku).
1. Dzielimy przez maksymalną przepustowość danego łącza. Uzyskujemy średnią procentową wartość.
1. Na podstawie obliczonego % oraz znajomości wykładniczego modelu opóźnień każdemu łączu przypisujemy wagę, zgodnie z funkcją wykładniczą;
  - 100% odpowiada wadze 10 000
  - 0% odpowiada wadze 0
  - przy przeliczaniu korzystamy ze wzoru: x^2
  - 50% odpowiada więc 2 500.
6. Za pomocą algorytmu Dijkstry dla każdej możliwej trasy obliczamy najkrótszą ścieżkę.
1. Posiadając informację o tym przez jaki port należy kierować pakiet adresowany do danego hosta (IP), dodajemy nowe wpisy w tablicach przepływów.


### Używane zmienne i struktury danych

| Typ  | Nazwa | Domyślna wartość | Opis |
| ------------- | ------------- | ------------- | ------------- |
| int  | POLLING_INTERVAL  | 5 | [s] - co ile zbieramy statystyki z portów |
| int | MAX_THR | 1e9 /8 | [B/s] - przepustowość łączy (raczej u nas przypuszczamy, że wszystkie łącza taką samą mają, ale jeśli nie to można dorzucić do struktury grafu jak bytesTx i wagi) |
| graph (networkx object) | topo | - | przechowuje aktualną topologię w postaci grafu |
| dict (string, string) : int | interfaces | - | np. interfaces[(Bydgoszcz, Warszawa)]: 2 -> oznacza, że Warszawa jest sąsiadem Bydgoszczy na jej porcie nr 2 |
| dict (string, string) : int | routing | - | np. routing[(Bydgoszcz, Olszytn)]: 2 -> oznacza, że ze switcha Bydgoszcz jeśli chcemy coś przesłać do Olsztyna to przez port nr 2 (czyli przez Warszawę) |


#### Dodatkowe dane zapisane w strukturze graph dla krawędzi (topo.edges(data=True)):
| Typ  | Nazwa | Domyślna wartość | Opis |
| ------------- | ------------- | ------------- | ------------- |
| long | topo.edges[‘bytesTx’] | 0 - ... | [B] - dane przesłane przez dany port |
| int | topo.edges[‘wagi’] | 0 - 10 000 | wyliczona na podstawie modelu waga na łączu |


## Inne przydatne komendy

#### Mininet

`dpctl dump-flows` - pokazuje wszystkie tablice przepływów; `sh ovs-ofctl dump-flows <switch_name>` - pokauje przepływy zainstalowane w danym switchu

`nodes` - listuje dostępne węzły; `net` - linki

#### System

`sudo mn -c` - czyszczenie danych Minineta

