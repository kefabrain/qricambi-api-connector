# QRicambi API Connector

Python client for the [QRicambi API](https://app.qricambi.com/dev/docs) — ricerca ricambi auto, gestione ordini, listini e veicoli.

## Installazione

```bash
pip install -e .
```

## Uso rapido

```python
from qricambi import QRicambiClient

client = QRicambiClient(token="your-jwt-token")

# Ricerca veicolo da targa
vehicle = client.vehicle_by_plate("AB123CD")
print(vehicle.manufacturer, vehicle.model, vehicle.engine_code)

# Ricerca prezzo e disponibilità
results = client.search_price_availability(
    supplier="SUPPLIER_NAME",
    skus=["1234567890"],
    brand_input="PIAGGIO",
)
for r in results:
    print(f"{r.code} — €{r.price} — disponibile: {r.availability.is_available}")

# Lista fornitori
suppliers = client.list_suppliers()

# Gestione ordini
orders = client.list_orders(q_order_number="Q-12345")

# Gestione listini prodotti
lists = client.list_product_lists()
new_list = client.create_product_list("Il mio listino")
client.add_product_list_items(new_list.id, [
    {"code": "ABC123", "brand": "PIAGGIO", "price": 15.50, "qta": 10}
])

# Estrazione entità da testo libero
entities = client.extract_entities("filtro olio Piaggio Porter 1.3 diesel")
```

## Endpoints disponibili

| Metodo | Endpoint | Descrizione |
|--------|----------|-------------|
| `list_suppliers()` | GET /mysupplier | Lista fornitori |
| `check_supplier()` | POST /checkmysupplier | Verifica credenziali fornitore |
| `extract_entities()` | POST /entity/retrieves | NLP: estrai entità da testo |
| `list_orders()` | GET /orders/list | Lista righe ordine |
| `add_order_row()` | POST /orders/row | Aggiungi riga ordine |
| `update_order_row()` | PUT /orders/row | Aggiorna riga ordine |
| `delete_order_rows()` | POST /orders/row/delete/bulk | Elimina righe (bulk) |
| `undo_delete_order_rows()` | POST /orders/row/delete/bulk/undo | Annulla eliminazione |
| `get_order_row_history()` | GET /orders/row/{id}/history | Storico riga ordine |
| `export_orders()` | POST /orders/export | Esporta ordini |
| `list_product_lists()` | GET /productlist | Indice listini |
| `create_product_list()` | POST /productlist | Crea listino |
| `delete_product_list()` | DELETE /productlist/{id} | Elimina listino |
| `get_product_list_items()` | GET /productlist/{id}/items | Items di un listino |
| `add_product_list_items()` | POST /productlist/{id}/items | Aggiungi items (max 1000) |
| `delete_product_list_items()` | DELETE /productlist/{id}/items | Rimuovi items (max 1000) |
| `update_product_list_items()` | PATCH /productlist/{id}/items | Aggiorna items (max 1000) |
| `search_price_availability()` | POST /searchpriceandavailability | Prezzi e disponibilità (max 3 SKU, 30s rate limit) |
| `vehicle_by_plate()` | GET /vehiclebyplate | Dati veicolo da targa italiana |

## Rate Limits

- `/searchpriceandavailability`: max 3 SKU per request, **attendere almeno 30 secondi** tra le chiamate (gestito automaticamente dal client con `respect_rate_limit=True`)
- Product list operations: max 1000 items per request

## Licenza

MIT
