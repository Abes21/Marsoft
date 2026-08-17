# Znane ograniczenia

1. **Monitoring = ICMP ping** – brak agentów/SNMP; stacje Windows z zaporą
   blokującą ping mogą być raportowane jako niedostępne.
2. **nmap w kontenerze na Windowsie** – brak skanu ARP całego LAN
   (sieć wirtualna WSL2); wykrywanie głównie hostów odpowiadających na ping.
3. **Brak powiadomień e-mail** – tylko w aplikacji (brak serwera SMTP).
4. **Limit logowań w pamięci procesu** – przy wielu workerach gunicorn
   licznik jest per-worker; w produkcji zalecany Redis/Memcached.
5. **HTTP bez TLS** – w produkcji zalecany reverse proxy z HTTPS.
6. **Brak integracji AD/LDAP/SSO** – konta lokalne aplikacji.
7. **Dane demo są syntetyczne** (RNF-16).
8. **Audyt i historia alertów są nieedytowalne** – celowe (RNF/RF-82).
9. **Jedna strefa czasowa** – czas serwera.
10. **DEBUG=True tylko w rozwoju** – w produkcji należy ustawić False
    i własny SECRET_KEY.
