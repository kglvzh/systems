import grpc
import inventory_pb2
import inventory_pb2_grpc
import pickle
import os

FILE_NAME = "items.dat"

def load_items():
    if os.path.exists(FILE_NAME):
        try:
            with open(FILE_NAME, 'rb') as f:
                data = pickle.load(f)
                if isinstance(data, list):
                    return data
                else:
                    return []
        except:
            return []
    return []

def save_items(items):
    try:
        with open(FILE_NAME, 'wb') as f:
            pickle.dump(items, f)
        print(f"💾 Сохранено {len(items)} товаров в файл")
    except:
        print("Ошибка сохранения")

def clear_all_data(stub):
    """Очистка данных и на сервере, и в локальном файле"""
    print("\n ПОЛНАЯ ОЧИСТКА ДАННЫХ ")
   
    # 1. Очищаем локальный файл
    if os.path.exists(FILE_NAME):
        os.remove(FILE_NAME)
        print("✓ Локальный файл items.dat удален")
   
    # 2. Очищаем сервер
    try:
        response = stub.ClearData(inventory_pb2.Empty())
        print(f"✓ Сервер: {response.message}")
    except Exception as e:
        print(f"✗ Ошибка при очистке сервера: {e}")
   
    print(" ОЧИСТКА ЗАВЕРШЕНА \n")

def run():
    channel = grpc.insecure_channel('localhost:50051')
    stub = inventory_pb2_grpc.InventoryControlStub(channel)
   
    print("МАССОВОЕ ОБНОВЛЕНИЕ ОСТАТКОВ")
   
    # Спрашиваем про очистку
    clear = input("\nОчистить ВСЕ данные (сервер + файл)? (y/n): ").strip().lower()
    if clear == 'y':
        clear_all_data(stub)
        # После очистки начинаем с пустым списком
        saved_items = []
    else:
        # Загружаем ранее сохраненные товары
        saved_items = load_items()
        if saved_items:
            print(f"\n📂 Загружено {len(saved_items)} ранее добавленных товаров:")
            for i, item in enumerate(saved_items):
                try:
                    pid = item.get('product_id', 'Неизвестно')
                    name = item.get('product_name', 'Без названия')
                    qty = item.get('quantity', 0)
                    print(f"  {i+1}. {pid} - {name} - {qty}")
                except:
                    print(f"  {i+1}. Ошибка чтения данных")
   
    items = []
   
    while True:
        print("\n--- Товар", len(items) + 1)
       
        pid = input("ID товара (Enter - закончить): ").strip()
        if not pid:
            break
           
        name = input("Название: ").strip()
        if not name:
            name = "Без названия"
           
        try:
            qty = int(input("Количество: "))
        except:
            print("Ошибка! Количество должно быть числом")
            continue
       
        items.append({
            'product_id': pid,
            'product_name': name,
            'quantity': qty
        })
        print("✓ Добавлено")
   
    # Если была очистка, saved_items уже пустой
    if clear == 'y':
        all_items = items
    else:
        all_items = saved_items + items
   
    if not all_items:
        print("Нет данных для отправки")
        return
   
    save_items(all_items)
   
    print(f"\n📤 Отправка {len(all_items)} товаров на сервер...")
   
    def gen():
        for item in all_items:
            try:
                pid = item.get('product_id', '')
                name = item.get('product_name', 'Без названия')
                qty = item.get('quantity', 0)
                print(f"→ {pid}: {qty}")
                yield inventory_pb2.StockItem(
                    product_id=pid,
                    product_name=name,
                    quantity=qty
                )
            except:
                print(f"→ Ошибка в данных, пропускаем")
                continue
   
    try:
        response = stub.BulkUpdateStock(gen())
        print("\n" + "-"*30)
        print(f"Всего: {response.total_processed}")
        print(f"Успешно: {response.successful_updates}")
        print(f"Ошибок: {response.failed_updates}")
        print(response.message)
    except grpc.RpcError as e:
        print(f"Ошибка: {e}")

if __name__ == '__main__':
    run()
