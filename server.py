import grpc
from concurrent import futures
import time

# Импортируем сгенерированные классы
import inventory_pb2
import inventory_pb2_grpc

class InventoryControlServicer(inventory_pb2_grpc.InventoryControlServicer):
   
    def __init__(self):
        self.stock_db = {}  # ЭТО ХРАНИЛИЩЕ ТЕПЕРЬ ЖИВЕТ ВСЕ ВРЕМЯ
        print("Сервер InventoryControl инициализирован")
   
    def BulkUpdateStock(self, request_iterator, context):
        """Client streaming RPC метод"""
        print("\n НАЧАЛО МАССОВОГО ОБНОВЛЕНИЯ ")
       
        total = 0
        success = 0
        failed = 0
       
        for stock_item in request_iterator:
            total += 1
            print(f"\nПолучен товар #{total}: {stock_item.product_id} - {stock_item.product_name} - {stock_item.quantity}")
           
            if stock_item.product_id and stock_item.quantity >= 0:
                # СОХРАНЯЕМ В БАЗУ (self.stock_db сохраняется между вызовами!)
                self.stock_db[stock_item.product_id] = {
                    'id': stock_item.product_id,
                    'name': stock_item.product_name,
                    'qty': stock_item.quantity
                }
                success += 1
                print(f"  ✓ СОХРАНЕНО")
            else:
                failed += 1
                print(f"  ✗ ОШИБКА")
       
        print(f"\nИТОГИ:")
        print(f"  Всего: {total}")
        print(f"  Успешно: {success}")
        print(f"  Ошибок: {failed}")
        print(f"  ВСЕГО ЗАПИСЕЙ В БД: {len(self.stock_db)}")
       
        # Показываем все текущие записи
        if self.stock_db:
            print(f"\nТЕКУЩИЕ ТОВАРЫ НА СКЛАДЕ:")
            for pid, data in self.stock_db.items():
                print(f"  {pid}: {data['name']} - {data['qty']} шт.")
       
        return inventory_pb2.UpdateSummary(
            total_processed=total,
            successful_updates=success,
            failed_updates=failed,
            message=f"Обновление завершено. Всего в БД: {len(self.stock_db)}"
        )
   
    def ClearData(self, request, context):
        """Очистка всех данных на сервере"""
        print("\n ОЧИСТКА ДАННЫХ ")
        count = len(self.stock_db)
        self.stock_db.clear()  # ВОТ ТУТ РЕАЛЬНО ОЧИЩАЕМ
        print(f"УДАЛЕНО ЗАПИСЕЙ: {count}")
        print(f"ТЕПЕРЬ В БД: {len(self.stock_db)} записей")
       
        return inventory_pb2.UpdateSummary(
            total_processed=0,
            successful_updates=0,
            failed_updates=0,
            message=f"Данные очищены. Удалено {count} записей"
        )

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
   
    inventory_pb2_grpc.add_InventoryControlServicer_to_server(
        InventoryControlServicer(), server
    )
   
    server.add_insecure_port('[::]:50051')
    server.start()

    print("СЕРВЕР ЗАПУЩЕН НА ПОРТУ 50051")
    print("Методы: BulkUpdateStock, ClearData")
    
    server.wait_for_termination()

if __name__ == '__main__':
    serve()